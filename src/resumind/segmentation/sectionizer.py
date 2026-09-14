import re
from typing import List, Dict
from resumind.segmentation.models import SectionBlock

SECTION_ALIASES = {
    "experience": ['experience', 'work experience', 'professional experience', 'employment', 'employment history', 'work history', 'career history', 'internships', 'professional background'],
    "education": ['education', 'academic background', 'academic history', 'qualifications', 'educational qualifications'],
    "skills": ['skills', 'technical skills', 'core skills', 'technical expertise', 'technologies', 'skills & technologies', 'competencies', 'technical skills / tools', 'technical skills & tools'],
    "summary": ['summary', 'professional summary', 'profile', 'professional profile', 'career summary', 'objective', 'career objective'],
    "projects": ['projects', 'academic projects', 'personal projects', 'technical projects', 'selected projects', 'key projects'],
    "contact": ['contact', 'contact information', 'personal information']
}

class Sectionizer:
    """
    Deterministic structural segmenter.
    """
    
    def __init__(self):
        self.reverse_alias_map = self._build_alias_map()
        
    def _build_alias_map(self) -> Dict[str, str]:
        alias_map = {}
        for canonical, aliases in SECTION_ALIASES.items():
            for alias in aliases:
                alias_map[alias] = canonical
        return alias_map
        
    def _normalize_heading(self, line: str) -> str:
        """Normalizes a line for heading comparison."""
        # Remove non-alphanumeric (except spaces) and lowercase
        line = re.sub(r"[^a-zA-Z0-9\s]", "", line)
        return re.sub(r"\s+", " ", line).strip().lower()

    def _evaluate_heading(self, line: str) -> tuple[str, float]:
        """
        Evaluates if a line is a heading.
        Returns (canonical_name, confidence). Returns (None, 0.0) if not a heading.
        """
        if not line or len(line) > 50:
            return None, 0.0
            
        norm_line = self._normalize_heading(line)
        
        canonical = self.reverse_alias_map.get(norm_line)
        
        # If it's an exact match in our alias map
        if canonical:
            # High confidence if it's uppercase or title case
            if line.isupper():
                return canonical, 0.95
            elif line.istitle():
                return canonical, 0.85
            else:
                return canonical, 0.70
                
        # If it is uppercase, short, and not in the map, it might be an unknown section
        if line.isupper() and 3 < len(line) < 30 and not re.search(r"\d", line):
            return "unknown", 0.60
            
        return None, 0.0

    def segment(self, lines: List[str]) -> List[SectionBlock]:
        """
        Segments cleaned lines into SectionBlocks.
        """
        sections: List[SectionBlock] = []
        
        current_section_name = "contact_header"
        current_heading = ""
        current_lines = []
        current_confidence = 1.0 # high confidence for implicit first section
        
        for line in lines:
            canonical, conf = self._evaluate_heading(line)
            
            if canonical and conf >= 0.60:
                # We found a new section! Save the current one if it has content (ignoring pure blanks)
                if any(l.strip() for l in current_lines):
                    sections.append(SectionBlock(
                        canonical_name=current_section_name,
                        original_heading=current_heading,
                        lines=current_lines,
                        confidence=current_confidence
                    ))
                
                # Start new section
                current_section_name = canonical
                current_heading = line
                current_lines = []
                current_confidence = conf
            else:
                current_lines.append(line)
                
        # Append the final section
        if current_lines and any(l.strip() for l in current_lines):
            sections.append(SectionBlock(
                canonical_name=current_section_name,
                original_heading=current_heading,
                lines=current_lines,
                confidence=current_confidence
            ))
            
        return sections
