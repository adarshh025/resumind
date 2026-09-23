import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from resumind.models.resume import (
    ResumeData, Metadata, CandidateProfile, Experience, Education, Project,
    CanonicalSkill, Entity
)
from resumind.segmentation.models import SectionBlock

logger = logging.getLogger(__name__)

ROLE_KEYWORDS = {
    'engineer', 'developer', 'analyst', 'architect', 'designer', 'consultant',
    'manager', 'director', 'lead', 'specialist', 'administrator', 'intern',
    'scientist', 'researcher', 'officer', 'head', 'vp', 'president', 'fellow',
    'programmer', 'strategist', 'artist', 'writer', 'technician', 'producer',
    'recruiter', 'coordinator', 'executive', 'assistant', 'representative',
    'associate', 'copywriter', 'student'
}

COMPANY_KEYWORDS = {
    'inc', 'llc', 'ltd', 'corp', 'corporation', 'technologies', 'technology',
    'labs', 'systems', 'solutions', 'studio', 'services', 'company', 'co',
    'group', 'capital', 'partners', 'media', 'digital', 'consulting', 'network',
    'bank', 'health', 'ventures', 'firm', 'logistics', 'freighthub', 'industries',
    'devices', 'institute', 'creativebox', 'pixelperfect', 'adverse', 'webflow'
}

DEGREE_REGEX = re.compile(
    r"\b(B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?|B\.?Sc|M\.?Sc|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|"
    r"BBA|MBA|B\.?Com|M\.?Com|Ph\.?D\.?|PhD|Diploma|Associate|Bachelor(?:'s)?(?:\s+of\s+[A-Za-z\s]+)?|"
    r"Master(?:'s)?(?:\s+of\s+[A-Za-z\s]+)?|Doctor of Philosophy|BCA|MCA|B\.?F\.?A\.?)\b",
    re.IGNORECASE
)

INSTITUTION_INDICATORS = re.compile(
    r"\b(University|College|Institute|School|Academy|Polytechnic|Conservatory|UC\s+[A-Za-z]+|SUNY)\b",
    re.IGNORECASE
)

DATE_PATTERN = re.compile(
    r"\(?((?:[A-Za-z]{3,9}\s+|[0-1]?\d/)?\d{4})\s*(?:[-–—\s\ufffd]|\bto\b)+\s*((?:[A-Za-z]{3,9}\s+|[0-1]?\d/)?\d{4}|[Pp]resent|[Cc]urrent|[Nn]ow)\)?",
    re.IGNORECASE
)


class ResumeAssembler:
    """
    Orchestrates the final unified resume model.
    Converts disjointed extractions into a traceable schema.
    """
    
    def assemble(
        self, 
        raw_text: str,
        cleaned_text: str,
        sections: List[SectionBlock],
        contact_info: Any,
        entities: List[Entity],
        skills: List[CanonicalSkill],
        file_name: str = "unknown"
    ) -> ResumeData:
        
        resume = ResumeData()
        
        # 1. Metadata
        resume.metadata = Metadata(
            file_name=file_name,
            file_type=file_name.split(".")[-1] if "." in file_name else "unknown",
            processing_timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        # 2. Contact & Sections & Texts
        resume.raw_text = raw_text
        resume.cleaned_text = cleaned_text
        resume.contact = contact_info
        resume.sections = [s.model_dump() for s in sections]
        resume.entities = entities
        resume.skills = skills
        
        # 3. Candidate
        resume.candidate = self._assemble_candidate(sections, entities, contact_info, resume.warnings)
        
        # 4. Summary
        resume.summary = self._assemble_summary(sections)
        
        # 5. Experience
        resume.experience = self._assemble_experience(sections, entities, skills, resume.warnings)
        
        # 6. Education
        resume.education = self._assemble_education(sections, entities, resume.warnings)
        
        # 7. Projects
        resume.projects = self._assemble_projects(sections, skills)
        
        return resume
        
    def _assemble_candidate(self, sections, entities, contact_info, warnings) -> CandidateProfile:
        candidate = CandidateProfile()
        
        # 1. Find candidate name from entities (validated by NER)
        for ent in entities:
            if ent.label == "CANDIDATE":
                candidate.name = ent.normalized_text.title()
                break
                
        # 2. Robust fallback if NER did not identify a candidate entity
        if not candidate.name:
            skip_words = {"resume", "curriculum vitae", "cv", "profile", "contact", "summary"}
            for sec in sections:
                if sec.canonical_name == "contact_header" and sec.lines:
                    for line in sec.lines:
                        cand_name = self._extract_fallback_name(line, skip_words)
                        if cand_name:
                            candidate.name = cand_name
                            warnings.append("Candidate name not found by NER. Extracting first valid line as fallback.")
                            break
                    if candidate.name:
                        break
                        
        # 3. Find location
        for ent in entities:
            if ent.label == "LOCATION" and any(m.section == "contact_header" for m in ent.mentions):
                candidate.location = ent.normalized_text.title()
                break
                
        return candidate

    def _extract_fallback_name(self, line: str, skip_words: set) -> Optional[str]:
        cleaned = line.strip()
        if not cleaned:
            return None
        # Reject markdown table syntax, decorative separators
        if any(sep in cleaned for sep in ["|---|", "===", "---", "___", "~~~", "+++"]):
            return None
        if len(set(cleaned.replace(" ", ""))) <= 3 and len(cleaned) > 5:
            return None
            
        # If pipe present, split and check segments
        if "|" in cleaned:
            segments = [s.strip(" >><<[]()'\"") for s in cleaned.split("|") if s.strip(" >><<[]()'\"")]
            for seg in segments:
                res = self._extract_fallback_name(seg, skip_words)
                if res:
                    return res
            return None
            
        # If comma-separated with title suffix
        if "," in cleaned:
            parts = [p.strip() for p in cleaned.split(",") if p.strip()]
            if len(parts) >= 2 and any(k in parts[1].lower() for k in ROLE_KEYWORDS):
                return self._extract_fallback_name(parts[0], skip_words)
                
        cand = re.sub(r"[><\[\]\(\)]", "", cleaned).strip()
        # Reject if contains email, URL, or digits
        if "@" in cand or "http" in cand or "www." in cand or any(ch.isdigit() for ch in cand):
            return None
            
        lower_cand = cand.lower()
        if lower_cand in skip_words:
            return None
            
        # Reject if matches job title keywords
        if any(k == lower_cand or lower_cand.startswith(k + " ") or lower_cand.endswith(" " + k) for k in ROLE_KEYWORDS):
            return None
            
        tokens = cand.split()
        if not (1 <= len(tokens) <= 4):
            return None
            
        for tok in tokens:
            if not re.match(r"^[A-Za-z][A-Za-z\.\'\-]*$", tok):
                return None
                
        return cand.title()

    def _assemble_summary(self, sections) -> str:
        for sec in sections:
            if sec.canonical_name == "summary":
                return "\n".join(sec.lines).strip()
        return None

    def _parse_experience_header_line(self, line_str: str, entities: List[Entity]) -> Tuple[Optional[str], Optional[str], List[str]]:
        line_clean = line_str.strip().lstrip("-•* >").strip()
        if not line_clean:
            return None, None, []

        dates = []
        for m in DATE_PATTERN.finditer(line_clean):
            dates.append(m.group(0).strip("()"))

        text = DATE_PATTERN.sub('', line_clean)
        text = re.sub(r"\(?(?:19\d{2}|20\d{2})\)?", '', text).strip(" ()[]|-,–—\ufffd")
        if not text:
            return None, None, dates

        # Check " at " or " @ "
        at_match = re.split(r'\s+(?:at|@)\s+', text, maxsplit=1, flags=re.IGNORECASE)
        if len(at_match) == 2:
            role = at_match[0].strip(" ,|-")
            org = at_match[1].strip(" ,|-")
            return role, org, dates

        # Delimiters: | or — or \ufffd or - or ,
        delims = re.split(r'\s*[|—\ufffd]\s*|\s+-\s+|,\s*', text)
        parts = [p.strip(" ()[]|-") for p in delims if p.strip(" ()[]|-")]

        if len(parts) >= 2:
            candidate_parts = []
            for p in parts:
                p_lower = p.lower()
                if re.match(r'^[A-Za-z\s]+,\s*[A-Z]{2}$', p) or any(loc in p_lower for loc in ['chicago', 'miami', 'atlanta', 'san francisco', 'new york', 'london', 'remote']):
                    continue
                candidate_parts.append(p)

            if len(candidate_parts) >= 2:
                p0, p1 = candidate_parts[0], candidate_parts[1]
                p0_lower, p1_lower = p0.lower(), p1.lower()
                p0_is_role = any(r in p0_lower for r in ROLE_KEYWORDS)
                p1_is_role = any(r in p1_lower for r in ROLE_KEYWORDS)
                p0_is_org = any(c in p0_lower for c in COMPANY_KEYWORDS)
                p1_is_org = any(c in p1_lower for c in COMPANY_KEYWORDS)

                if any(e.label == "ORGANIZATION" and any(m.text.lower() == p0_lower for m in e.mentions) for e in entities):
                    p0_is_org = True
                if any(e.label == "ORGANIZATION" and any(m.text.lower() == p1_lower for m in e.mentions) for e in entities):
                    p1_is_org = True

                if p0_is_role and not p1_is_role:
                    return p0, p1, dates
                elif p1_is_role and not p0_is_role:
                    return p1, p0, dates
                elif p0_is_org and not p1_is_org:
                    return p1, p0, dates
                elif p1_is_org and not p0_is_org:
                    return p0, p1, dates
                else:
                    return p0, p1, dates
            elif len(candidate_parts) == 1:
                parts = candidate_parts

        lower = text.lower()
        is_role = any(r in lower for r in ROLE_KEYWORDS)
        is_org = any(c in lower for c in COMPANY_KEYWORDS) or any(e.label == "ORGANIZATION" and any(m.text.lower() == lower for m in e.mentions) for e in entities)

        if is_role and not is_org:
            return text, None, dates
        elif is_org:
            return None, text, dates
        elif len(text.split()) <= 5:
            return text, None, dates

        return None, None, dates

    def _assemble_experience(self, sections, entities, skills, warnings) -> List[Experience]:
        exps = []
        for sec in sections:
            if sec.canonical_name != "experience":
                continue
                
            current_exp = None
            
            for line in sec.lines:
                line_str = line.strip()
                if not line_str:
                    continue
                    
                is_bullet = line_str.startswith("-") or line_str.startswith("•") or line_str.startswith("*")
                
                if is_bullet:
                    if current_exp is not None:
                        current_exp.description.append(line_str.lstrip("-•* ").strip())
                    continue

                role_cand, org_cand, dates_cand = self._parse_experience_header_line(line_str, entities)

                # Check if this line marks the beginning of a NEW experience entry
                should_start_new = False
                if current_exp is None:
                    if role_cand or org_cand or dates_cand:
                        should_start_new = True
                elif current_exp.organization and org_cand:
                    should_start_new = True
                elif current_exp.role and role_cand and not org_cand:
                    if current_exp.description or current_exp.organization:
                        should_start_new = True
                elif role_cand and org_cand:
                    if current_exp.role or current_exp.organization:
                        should_start_new = True

                if should_start_new:
                    current_exp = Experience()
                    exps.append(current_exp)

                if current_exp is not None:
                    if role_cand and not current_exp.role:
                        current_exp.role = role_cand
                    if org_cand and not current_exp.organization:
                        current_exp.organization = org_cand.title()

                    if dates_cand:
                        d_str = dates_cand[0]
                        d_parts = re.split(r'\s*(?:[-–—\ufffd]|\bto\b)\s*', d_str, flags=re.IGNORECASE)
                        if len(d_parts) >= 2:
                            current_exp.start_date = d_parts[0].strip()
                            current_exp.end_date = d_parts[1].strip()
                            if any(k in d_parts[1].lower() for k in ["present", "current", "now"]):
                                current_exp.is_current = True
                        else:
                            if not current_exp.start_date:
                                current_exp.start_date = d_str
                            elif not current_exp.end_date and d_str != current_exp.start_date:
                                current_exp.end_date = d_str
                                if any(k in d_str.lower() for k in ["present", "current", "now"]):
                                    current_exp.is_current = True

                    # Also propagate is_current from entities
                    for e in entities:
                        if e.label == "DATE" and any(m.text in line_str for m in e.mentions):
                            for m in e.mentions:
                                if m.is_current:
                                    current_exp.is_current = True
                                
            # Bind skills
            for exp in exps:
                desc_text = " ".join(exp.description)
                linked_skills = []
                for s in skills:
                    for m in s.mentions:
                        if m.section == "experience" and m.raw_text in desc_text:
                            if s.canonical_name not in linked_skills:
                                linked_skills.append(s.canonical_name)
                exp.skills = linked_skills
                if desc_text:
                    exp.evidence["description_source"] = desc_text
                    
        return exps

    def _parse_education_line(self, line_str: str, entities: List[Entity]) -> Tuple[Optional[str], Optional[str], List[str], Optional[str]]:
        line_clean = line_str.strip().lstrip("-•* >").strip()
        if not line_clean:
            return None, None, [], None

        lower = line_clean.lower()

        grade = None
        if 'gpa' in lower or 'cgpa' in lower or '%' in lower:
            gpa_match = re.search(r'(?:c?gpa:?\s*)?(\d\.\d+(?:\s*/\s*\d\.\d+)?|\d{2,3}%)', line_clean, re.IGNORECASE)
            if gpa_match:
                grade = gpa_match.group(0).strip()

        dates = []
        for m in DATE_PATTERN.finditer(line_clean):
            dates.append(m.group(0).strip("()"))
        year_match = re.search(r"\(?(19\d{2}|20\d{2})\)?", line_clean)
        if year_match and not dates:
            dates.append(year_match.group(1))

        text = DATE_PATTERN.sub('', line_clean)
        text = re.sub(r"\(?(?:19\d{2}|20\d{2})\)?", '', text)
        if grade:
            text = text.replace(grade, '')
        text = text.strip(" ()[]|-,–—\ufffd")

        if not text:
            return None, None, dates, grade

        has_degree = bool(DEGREE_REGEX.search(text))
        has_inst = bool(INSTITUTION_INDICATORS.search(text))

        for ent in entities:
            if ent.label == "ORGANIZATION" and any(m.text.lower() in text.lower() for m in ent.mentions):
                if not any(d in ent.normalized_text.lower() for d in ["bachelor", "master", "phd", "b.s", "m.s"]):
                    has_inst = True
                    break

        degree = None
        institution = None

        if has_degree and has_inst:
            delims = re.split(r'\s*[|—\ufffd]\s*|\s+-\s+|,\s*', text)
            parts = [p.strip(" ()[]|-") for p in delims if p.strip(" ()[]|-")]
            if len(parts) >= 2:
                p0_deg = bool(DEGREE_REGEX.search(parts[0]))
                p1_deg = bool(DEGREE_REGEX.search(parts[1]))
                p0_inst = bool(INSTITUTION_INDICATORS.search(parts[0]))
                p1_inst = bool(INSTITUTION_INDICATORS.search(parts[1]))

                if p0_deg and p1_inst:
                    degree, institution = parts[0], parts[1]
                elif p1_deg and p0_inst:
                    degree, institution = parts[1], parts[0]
                else:
                    degree, institution = parts[0], parts[1]
            else:
                degree = text
        elif has_degree:
            degree = text
        elif has_inst:
            institution = text
        elif len(text.split()) <= 6 and not any(k in lower for k in ['coursework', 'publications', 'selected', 'awards', 'honors', 'graduation']):
            institution = text

        return degree, institution, dates, grade

    def _assemble_education(self, sections, entities, warnings) -> List[Education]:
        edus = []
        for sec in sections:
            if sec.canonical_name != "education":
                continue
                
            current_edu = None
            
            for line in sec.lines:
                line_str = line.strip()
                if not line_str:
                    continue
                    
                is_bullet = line_str.startswith("-") or line_str.startswith("•") or line_str.startswith("*")
                if is_bullet:
                    continue

                deg, inst, dates, grade = self._parse_education_line(line_str, entities)

                lower = line_str.lower()
                if any(k in lower for k in ["coursework", "publications", "selected", "awards", "honors"]) and not deg and not inst:
                    continue

                should_start_new = False
                if current_edu is None:
                    if deg or inst:
                        should_start_new = True
                elif deg and current_edu.degree:
                    should_start_new = True
                elif inst and current_edu.institution and not deg:
                    if current_edu.degree or current_edu.start_date:
                        should_start_new = True

                if should_start_new:
                    current_edu = Education()
                    edus.append(current_edu)

                if current_edu is not None:
                    if deg and not current_edu.degree:
                        current_edu.degree = deg
                    if inst and not current_edu.institution:
                        current_edu.institution = inst.title()
                    if grade and not current_edu.grade:
                        current_edu.grade = grade
                    if dates:
                        d_str = dates[0]
                        d_parts = re.split(r'\s*(?:[-–—\ufffd]|\bto\b)\s*', d_str, flags=re.IGNORECASE)
                        if len(d_parts) >= 2:
                            current_exp_start = d_parts[0].strip()
                            current_exp_end = d_parts[1].strip()
                            if not current_edu.start_date:
                                current_edu.start_date = current_exp_start
                            if not current_edu.end_date:
                                current_edu.end_date = current_exp_end
                        else:
                            if not current_edu.start_date:
                                current_edu.start_date = d_str
                            elif not current_edu.end_date and d_str != current_edu.start_date:
                                current_edu.end_date = d_str
                                
        return edus
        
    def _assemble_projects(self, sections, skills) -> List[Project]:
        projs = []
        for sec in sections:
            if sec.canonical_name != "projects":
                continue
                
            current_proj = None
            
            for line in sec.lines:
                line_str = line.strip()
                if not line_str:
                    continue
                    
                is_bullet = line_str.startswith("-") or line_str.startswith("•")
                
                if not is_bullet and current_proj is None:
                    current_proj = Project()
                    current_proj.name = line_str
                    projs.append(current_proj)
                elif not is_bullet and current_proj is not None and current_proj.description:
                    current_proj = Project()
                    current_proj.name = line_str
                    projs.append(current_proj)
                elif current_proj is not None:
                    if is_bullet:
                        if not current_proj.description:
                            current_proj.description = ""
                        current_proj.description += line_str.lstrip("-• ").strip() + " "
                    else:
                        if not current_proj.description:
                            current_proj.description = line_str
                            
            # Bind skills
            for proj in projs:
                linked_skills = []
                for s in skills:
                    for m in s.mentions:
                        if m.section == "projects" and proj.description and m.raw_text in proj.description:
                            if s.canonical_name not in linked_skills:
                                linked_skills.append(s.canonical_name)
                proj.technologies = linked_skills
                if proj.description:
                    proj.evidence["description_source"] = proj.description.strip()
                    proj.description = proj.description.strip()
                    
        return projs

