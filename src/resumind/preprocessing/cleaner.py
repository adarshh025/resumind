import re
import unicodedata
from typing import List

BULLET_CHARS = {"•", "●", "▪", "◦", "○", "▸", "►", "–", "—", "*"}

class ResumeCleaner:
    """
    Non-destructive text cleaner for raw resume text.
    """
    
    def clean(self, raw_text: str) -> List[str]:
        """
        Cleans the raw text line by line.
        
        Args:
            raw_text (str): The raw extracted text from the document.
            
        Returns:
            List[str]: A list of cleaned lines.
        """
        lines = raw_text.splitlines()
        cleaned_lines = []
        
        for line in lines:
            # 1. Unicode Normalization (NFKC to preserve semantics but normalize spacing/composed chars)
            line = unicodedata.normalize("NFKC", line)
            
            # 2. Control characters removal (excluding valid whitespace)
            # Remove characters in the 'C' (Other, Control) category, but keep tabs/newlines
            line = "".join(ch for ch in line if unicodedata.category(ch)[0] != "C" or ch in {"\t", "\n", "\r"})
            
            # 3. Whitespace normalization (collapse multiple spaces to one, strip ends)
            line = re.sub(r"[ \t]+", " ", line).strip()
            
            # 4. Bullet normalization
            # If line starts with a known bullet character, canonicalize to "-"
            if line and line[0] in BULLET_CHARS:
                # E.g., "• Software Engineer" -> "- Software Engineer"
                line = "- " + line[1:].strip()
                
            # 5. Noise filtering (Page markers)
            # e.g., "Page 1 of 2", "Page 2"
            if self._is_page_marker(line):
                continue
                
            # Keep blank lines as they are structural signals, but represent them consistently
            cleaned_lines.append(line)
            
        return cleaned_lines
        
    def _is_page_marker(self, line: str) -> bool:
        """Heuristic to detect if a line is just a page marker."""
        lower_line = line.lower()
        if re.match(r"^page\s*\d+\s*(of\s*\d+)?$", lower_line):
            return True
        # Match standalone page numbers if they are exactly something like "1 / 2"
        if re.match(r"^\d+\s*/\s*\d+$", lower_line):
            return True
        return False
