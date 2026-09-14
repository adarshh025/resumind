from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DocumentExtractionResult(BaseModel):
    """
    Internal representation of an extracted document.
    """
    filename: str
    source_format: str
    raw_text: str
    page_count: Optional[int] = None
    status: str  # "SUCCESS", "TEXT_NOT_EXTRACTABLE", "ERROR"
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
