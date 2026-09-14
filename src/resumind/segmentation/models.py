from pydantic import BaseModel, Field
from typing import List

class SectionBlock(BaseModel):
    """
    Internal representation of a segmented resume section.
    """
    canonical_name: str     # e.g., "experience", "education", "unknown", "contact_header"
    original_heading: str   # e.g., "PROFESSIONAL EXPERIENCE"
    lines: List[str]        # Preserved line structure of the section
    confidence: float       # 0.0 to 1.0 based on structural signals
