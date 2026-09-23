import logging
import re
from typing import List, Dict, Tuple
from resumind.models.resume import Entity, EntityMention
from resumind.segmentation.models import SectionBlock

logger = logging.getLogger(__name__)

# Basic tech skill vocabulary has been moved to the dedicated ontology in data/skills.json


class SemanticEntityExtractor:
    """
    Extracts semantic entities (Candidate, Organization, Date, Location, Skill)
    using a hybrid NLP pipeline (spaCy) and section-aware heuristics.
    """
    
    def __init__(self):
        self.nlp = None
        self._load_spacy()
        
    def _load_spacy(self):
        try:
            import spacy
            # Load the model but we don't need the dependency parser for basic NER
            self.nlp = spacy.load("en_core_web_sm", disable=["parser"])
        except ImportError:
            logger.warning("spaCy is not installed. Semantic extraction will be limited.")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' is not installed.")
            
    def extract(self, sections: List[SectionBlock]) -> List[Entity]:
        # Deduplication registry: (normalized_text, label) -> Entity
        entity_registry: Dict[Tuple[str, str], Entity] = {}
        
        def _add_mention(text: str, label: str, section_name: str, source: str, is_current: bool = None):
            norm_text = text.lower().strip()
            
            # Post-processing / cleaning
            if label == "ORGANIZATION":
                # Remove common noise tokens picked up by generic NER
                norm_text = re.sub(r"^(at|for)\s+", "", norm_text)
                
            key = (norm_text, label)
            
            mention = EntityMention(
                text=text.strip(),
                section=section_name,
                source=source,
                is_current=is_current
            )
            
            if key not in entity_registry:
                entity_registry[key] = Entity(
                    normalized_text=norm_text,
                    label=label,
                    mentions=[]
                )
                
            # Avoid duplicate identical mentions in the same section for the same entity
            if not any(m.text == mention.text and m.section == mention.section for m in entity_registry[key].mentions):
                entity_registry[key].mentions.append(mention)

        # 1. Candidate Name (Heuristic + NER)
        self._detect_candidate(sections, _add_mention)
            
        for section in sections:
            for line in section.lines:
                text_line = line.strip()
                if not text_line:
                    continue
                    
                # 2. Date Extraction (Regex)
                self._extract_dates_regex(text_line, section.canonical_name, _add_mention)
                
                # 3. Semantic Extraction (spaCy)
                if self.nlp:
                    doc = self.nlp(text_line)
                    for ent in doc.ents:
                        if ent.label_ == "ORG":
                            _add_mention(ent.text, "ORGANIZATION", section.canonical_name, "spacy")
                        elif ent.label_ in ["GPE", "LOC"]:
                            _add_mention(ent.text, "LOCATION", section.canonical_name, "spacy")
                        # Ignore PERSON to avoid polluting with references and false positives
                        
        return list(entity_registry.values())
        
    JOB_TITLE_KEYWORDS = {
        "engineer", "developer", "analyst", "architect", "designer", "consultant",
        "manager", "director", "specialist", "administrator", "intern", "student",
        "researcher", "scientist", "lead", "coordinator", "representative",
        "executive", "officer", "founder", "freelancer", "associate", "assistant",
        "curriculum vitae", "resume", "cv", "profile", "summary", "contact",
        "experience", "education", "skills", "projects", "portfolio", "references",
        "details", "information", "statement", "objective", "certifications"
    }

    def _extract_candidate_name_from_line(self, line: str) -> tuple[str, bool]:
        """
        Extracts a clean, plausible candidate name from a raw header line.
        Handles pipe separators ('Name | email | phone'), comma title suffixes
        ('Name, Cloud Architect'), and rejects decorative/table artifacts.
        Returns (candidate_name, is_spacy_person) or (None, False).
        """
        if not line or not re.search(r"[a-zA-Z]", line):
            return None, False

        # Filter out decorative dividers and table borders
        if len(line) >= 3 and re.match(r"^[|\-=_~*+:\s#^`\.]{3,}$", line):
            return None, False

        # Clean decorative bracket wrappers e.g. '[START PROFILE] >> NINA WILLIAMS <<'
        cleaned = re.sub(r"\[.*?\]", "", line).strip()
        cleaned = re.sub(r"^[|\s>~*#\-\+]+", "", cleaned).strip()
        cleaned = re.sub(r"[|\s>~*#\-\+]+$", "", cleaned).strip()
        if not cleaned:
            return None, False

        # Check for pipe-delimited contact blocks e.g. "David Chen | david@email.com | 415-555-1122"
        if "|" in cleaned:
            segments = [s.strip(" >><<[]()'\"") for s in re.split(r"\|+", cleaned) if s.strip(" >><<[]()'\"")]
            for seg in segments:
                cand, is_p = self._extract_candidate_name_from_line(seg)
                if cand:
                    return cand, is_p
            return None, False

        # Check for comma-separated title suffix e.g. "Priya Patel, Cloud Solutions Architect"
        if "," in cleaned:
            parts = [p.strip() for p in cleaned.split(",") if p.strip()]
            if len(parts) >= 2:
                lower_second = parts[1].lower()
                if any(k in lower_second for k in ["engineer", "architect", "developer", "analyst", "manager", "lead", "director", "esq", "phd"]):
                    cand, is_p = self._extract_candidate_name_from_line(parts[0])
                    if cand:
                        return cand, is_p

        # Strip remaining enclosing bracket/quote noise
        cand = re.sub(r"[><\[\]\(\)]", "", cleaned).strip()
        
        # Reject if line contains email, URL, or telephone indicators
        if "@" in cand or "http" in cand or "www." in cand:
            return None, False
        if any(ch.isdigit() for ch in cand):
            return None, False

        tokens = cand.split()
        if not (1 <= len(tokens) <= 4):
            return None, False

        lower_cand = cand.lower()
        # Reject if the entire phrase is a job title keyword or heading
        if any(k == lower_cand or lower_cand.startswith(k + " ") or lower_cand.endswith(" " + k) for k in self.JOB_TITLE_KEYWORDS):
            return None, False

        # Check that tokens look like valid human name components (allow initials and hyphens)
        for tok in tokens:
            if not re.match(r"^[A-Za-z][A-Za-z\.\'\-]*$", tok):
                return None, False

        # Validate with spaCy NER if available
        is_person = False
        if self.nlp:
            doc = self.nlp(cand)
            # If spaCy tags GPE/LOC, it is a location, not a person
            if any(ent.label_ in ["GPE", "LOC"] for ent in doc.ents):
                return None, False
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    is_person = True
                    break

        return cand.title(), is_person

    def _detect_candidate(self, sections: List[SectionBlock], add_mention_fn):
        """
        Attempts to detect the candidate name from the contact_header using deterministic heuristics and NER.
        """
        candidates = []
        
        for section in sections:
            if section.canonical_name == "contact_header":
                for idx, line in enumerate(section.lines):
                    name_candidate, is_person = self._extract_candidate_name_from_line(line)
                    if name_candidate:
                        # Score candidate: spaCy person bonus, position bonus
                        score = 1.0 + (1.5 if is_person else 0.0) + (1.0 / (idx + 1))
                        candidates.append((score, name_candidate, is_person))

        if candidates:
            # Sort by score descending and take the best candidate
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_name, is_person = candidates[0]
            add_mention_fn(best_name, "CANDIDATE", "contact_header", "spacy" if is_person else "heuristic")
                        
    def _extract_dates_regex(self, line: str, section_name: str, add_mention_fn):
        """
        Extracts robust date spans and "Present" markers.
        """
        # Ranges: 2021 - 2024, Jan 2021 - Present, 01/2021 - Current
        range_pattern = re.compile(r"((?:[A-Za-z]{3,9}\s+|[0-1]?\d/)?\d{4})\s*[-–to]+\s*((?:[A-Za-z]{3,9}\s+|[0-1]?\d/)?\d{4}|[Pp]resent|[Cc]urrent|[Nn]ow)", re.IGNORECASE)
        
        for match in range_pattern.finditer(line):
            start = match.group(1).strip()
            end = match.group(2).strip()
            
            add_mention_fn(start, "DATE", section_name, "regex", is_current=False)
            
            is_curr = end.lower() in ["present", "current", "now"]
            add_mention_fn(end, "DATE", section_name, "regex", is_current=is_curr)
            
        # Standalone years
        year_pattern = re.compile(r"\b(19\d{2}|20\d{2})\b")
        for match in year_pattern.finditer(line):
            add_mention_fn(match.group(1), "DATE", section_name, "regex", is_current=False)
