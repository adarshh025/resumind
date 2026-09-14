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
        
    def _detect_candidate(self, sections: List[SectionBlock], add_mention_fn):
        """
        Attempts to detect the candidate name from the contact_header.
        """
        for section in sections:
            if section.canonical_name == "contact_header":
                for line in section.lines:
                    text = line.strip()
                    if not text:
                        continue
                        
                    # Ignore lines with contact indicators
                    if "@" in text or "http" in text or "www." in text:
                        continue
                        
                    # Ignore lines with digits (phones, addresses)
                    if any(char.isdigit() for char in text):
                        continue
                        
                    # Token count 1 to 4 is reasonable for a name
                    tokens = text.split()
                    if 1 <= len(tokens) <= 4:
                        # Ensure we don't accidentally pick up a job title
                        # e.g., "Software Engineer"
                        lower_text = text.lower()
                        if any(title in lower_text for title in ["engineer", "developer", "manager", "student", "intern", "curriculum vitae", "resume"]):
                            continue

                        is_person = False
                        if self.nlp:
                            doc = self.nlp(text)
                            for ent in doc.ents:
                                if ent.label_ == "PERSON":
                                    is_person = True
                                    break
                                    
                        add_mention_fn(text, "CANDIDATE", "contact_header", "spacy" if is_person else "heuristic")
                        return # Only take the very first plausible candidate
                        
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
