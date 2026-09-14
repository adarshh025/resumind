import json
import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path

from resumind.models.resume import CanonicalSkill, SkillMention
from resumind.segmentation.models import SectionBlock

logger = logging.getLogger(__name__)

class SkillExtractor:
    """
    Advanced context-aware Skill Extractor.
    Resolves aliases, disambiguates ambiguous terms, and tracks extraction evidence.
    """
    def __init__(self, ontology_path: Optional[str] = None):
        if not ontology_path:
            base_dir = Path(__file__).parent.parent
            ontology_path = base_dir / "data" / "skills.json"
            
        self.ontology_path = Path(ontology_path)
        
        # lower_alias -> canonical_record
        self.canonical_map: Dict[str, dict] = {} 
        
        # Compiled patterns for O(1) compilation overhead during parsing
        self.compiled_patterns: List[Tuple[re.Pattern, str, dict]] = []
        
        self._load_ontology()
        
    def _load_ontology(self):
        if not self.ontology_path.exists():
            raise FileNotFoundError(f"Skill ontology not found at {self.ontology_path}")
            
        with open(self.ontology_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for entry in data:
            canonical = entry["canonical"]
            cat = entry.get("category", "Uncategorized")
            is_ambiguous = entry.get("ambiguous", False)
            
            record = {
                "canonical": canonical,
                "category": cat,
                "ambiguous": is_ambiguous
            }
            
            # Map canonical name
            self.canonical_map[canonical.lower()] = record
            
            # Map aliases
            for alias in entry.get("aliases", []):
                self.canonical_map[alias.lower()] = record

        # Pre-compile regex for performance
        # We sort by length descending so that longer aliases match before shorter ones
        # e.g., "scikit-learn" matches before "c" if they were somehow related
        sorted_tokens = sorted(self.canonical_map.keys(), key=len, reverse=True)
        
        for token_lower in sorted_tokens:
            record = self.canonical_map[token_lower]
            escaped_token = re.escape(token_lower)
            
            # Smart boundaries
            prefix = r"\b" if re.match(r"^\w", token_lower) else r"(?<!\w)"
            
            # For suffix, if it ends in word char, use \b. 
            # If it ends in +, avoid matching if there are MORE pluses (like C+++)
            if re.search(r"\w$", token_lower):
                suffix = r"\b"
            elif token_lower.endswith("+"):
                suffix = r"(?!\+|#|\w)"
            else:
                suffix = r"(?!\w)"
                
            # Version capture regex: optional space followed by numbers separated by dots
            # e.g. "Python 3.12", "React 18"
            version_regex = r"(?:\s+(v?\d+(?:\.\d+)*))?"
            
            pattern = re.compile(f"{prefix}({escaped_token}){suffix}{version_regex}", re.IGNORECASE)
            self.compiled_patterns.append((pattern, token_lower, record))

    def _is_valid_context_for_ambiguous(self, token: str, text: str, section_name: str) -> bool:
        """
        Validates whether an ambiguous skill like 'Go' or 'C' appears in a technical context.
        """
        # Technical sections are inherently safe
        if section_name in ["skills", "projects", "experience", "certifications"]:
            return True
            
        # Check surrounding text for technical context in summary or unknown sections
        lower_text = text.lower()
        context_keywords = [
            "experience with", "proficient in", "using", "developed", 
            "built with", "knowledge of", "technologies", "framework", 
            "language", "database", "programming in", "written in"
        ]
        
        for kw in context_keywords:
            if kw in lower_text:
                return True
                
        return False
        
    def extract(self, sections: List[SectionBlock]) -> List[CanonicalSkill]:
        extracted: Dict[str, CanonicalSkill] = {}
        
        for section in sections:
            sec_name = section.canonical_name
            for line in section.lines:
                
                # We need to ensure we don't double extract if a string is matched by multiple patterns
                # (e.g. if 'React.js' matches, we shouldn't also match 'React' in the exact same span).
                # Since we sorted by length, we can track matched indices.
                matched_indices = set()
                
                for pattern, token_lower, record in self.compiled_patterns:
                    for match in pattern.finditer(line):
                        start_idx, end_idx = match.span(1)
                        
                        # Check if this exact span was already claimed by a longer alias
                        if any(idx in matched_indices for idx in range(start_idx, end_idx)):
                            continue
                            
                        matched_text = match.group(1)
                        version = match.group(2) if len(match.groups()) > 1 else None
                        
                        canonical_name = record["canonical"]
                        
                        # Guard for ambiguous skills
                        if record["ambiguous"]:
                            if not self._is_valid_context_for_ambiguous(matched_text, line, sec_name):
                                continue
                                
                        # Claim the indices
                        matched_indices.update(range(start_idx, end_idx))
                        
                        # Determine match type
                        match_type = "exact" if matched_text.lower() == canonical_name.lower() else "alias"
                        
                        # Add to results
                        if canonical_name not in extracted:
                            extracted[canonical_name] = CanonicalSkill(
                                canonical_name=canonical_name,
                                category=record["category"],
                                mentions=[]
                            )
                            
                        # Avoid duplicate mentions in the exact same section for the same version
                        is_duplicate = False
                        for m in extracted[canonical_name].mentions:
                            if m.raw_text == matched_text and m.section == sec_name and m.version == version:
                                is_duplicate = True
                                break
                                
                        if not is_duplicate:
                            extracted[canonical_name].mentions.append(SkillMention(
                                raw_text=matched_text,
                                section=sec_name,
                                match_type=match_type,
                                confidence="high",
                                version=version
                            ))
                            
        return list(extracted.values())
