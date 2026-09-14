import logging
from datetime import datetime
from typing import List, Dict, Any

from resumind.models.resume import (
    ResumeData, Metadata, CandidateProfile, Experience, Education, Project,
    CanonicalSkill, Entity
)
from resumind.segmentation.models import SectionBlock

logger = logging.getLogger(__name__)

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
        
        # Find candidate name from entities
        for ent in entities:
            if ent.label == "CANDIDATE":
                candidate.name = ent.normalized_text.title()
                break
                
        if not candidate.name:
            warnings.append("Candidate name not found by NER. Extracting first valid line as fallback.")
            skip_words = {"resume", "curriculum vitae", "cv", "profile"}
            for sec in sections:
                if sec.canonical_name == "contact_header" and sec.lines:
                    for line in sec.lines:
                        line_clean = line.strip()
                        if line_clean and line_clean.lower() not in skip_words:
                            candidate.name = line_clean.title()
                            break
                    if candidate.name:
                        break
                
        # Find location
        for ent in entities:
            if ent.label == "LOCATION" and any(m.section == "contact_header" for m in ent.mentions):
                candidate.location = ent.normalized_text.title()
                break
                
        return candidate
        
    def _assemble_summary(self, sections) -> str:
        for sec in sections:
            if sec.canonical_name == "summary":
                return "\n".join(sec.lines).strip()
        return None
        
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
                    
                is_bullet = line_str.startswith("-") or line_str.startswith("•")
                
                # Check for organizations in this line
                org = next((e for e in entities if e.label == "ORGANIZATION" and any(m.text in line_str for m in e.mentions)), None)
                dates = [e for e in entities if e.label == "DATE" and any(m.text in line_str for m in e.mentions)]
                
                if org or dates or (not is_bullet and current_exp is None):
                    if current_exp is None or (org and current_exp.organization):
                        current_exp = Experience()
                        exps.append(current_exp)
                        
                if current_exp is not None:
                    if org and not current_exp.organization:
                        current_exp.organization = org.normalized_text.title()
                        
                    if dates:
                        for date_ent in dates:
                            for m in date_ent.mentions:
                                if m.text in line_str:
                                    if not current_exp.start_date:
                                        current_exp.start_date = m.text
                                    elif not current_exp.end_date and m.text != current_exp.start_date:
                                        current_exp.end_date = m.text
                                    if m.is_current:
                                        current_exp.is_current = True
                                        
                    if is_bullet:
                        current_exp.description.append(line_str.lstrip("-• ").strip())
                    elif not org and not dates and not current_exp.role:
                        current_exp.role = line_str
                        
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
                    
                org = next((e for e in entities if e.label == "ORGANIZATION" and any(m.text in line_str for m in e.mentions)), None)
                dates = [e for e in entities if e.label == "DATE" and any(m.text in line_str for m in e.mentions)]
                
                lower_line = line_str.lower()
                is_degree = any(deg in lower_line for deg in ["b.tech", "m.tech", "b.sc", "m.sc", "bachelor", "master", "phd", "b.e"])
                
                # Ignore organization entity if the line is clearly a degree
                if is_degree:
                    org = None
                
                if org or current_edu is None:
                    # Only split if we already have a reasonably complete block (has an institution AND either a degree or a date)
                    if current_edu is None or (current_edu.institution and (current_edu.degree or current_edu.start_date)):
                        current_edu = Education()
                        edus.append(current_edu)
                        
                if current_edu is not None:
                    if org:
                        if not current_edu.institution:
                            current_edu.institution = org.normalized_text.title()
                        else:
                            # if we already have one but didn't split, it might be a false positive from spacy
                            # or just part of a longer name. We append it.
                            current_edu.institution += f", {org.normalized_text.title()}"
                        
                    if dates:
                        for date_ent in dates:
                            for m in date_ent.mentions:
                                if m.text in line_str:
                                    if not current_edu.start_date:
                                        current_edu.start_date = m.text
                                    elif not current_edu.end_date and m.text != current_edu.start_date:
                                        current_edu.end_date = m.text
                                    
                    # Basic degree check
                    if is_degree and not current_edu.degree:
                        current_edu.degree = line_str
                        
                    # Grade check
                    if ("cgpa" in lower_line or "gpa" in lower_line or "%" in lower_line) and not current_edu.grade:
                        current_edu.grade = line_str
                        
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
