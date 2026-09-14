from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from resumind.models.resume import ResumeData

class APIErrorDetail(BaseModel):
    code: str
    message: str

class APIErrorResponse(BaseModel):
    error: APIErrorDetail

class ParseResponse(BaseModel):
    status: str = "success"
    resume: Optional[ResumeData] = None
    warnings: List[str] = Field(default_factory=list)

class HealthResponse(BaseModel):
    status: str = "ok"
