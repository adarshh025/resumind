from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PhoneExtracted(BaseModel):
    raw: str
    normalized: str

class ContactInfo(BaseModel):
    emails: List[str] = Field(default_factory=list)
    phones: List[PhoneExtracted] = Field(default_factory=list)
    linkedin: List[str] = Field(default_factory=list)
    github: List[str] = Field(default_factory=list)
    portfolios: List[str] = Field(default_factory=list)
    other_urls: List[str] = Field(default_factory=list)
    
    @property
    def email(self) -> Optional[str]:
        return self.emails[0] if self.emails else None
        
    @property
    def phone(self) -> Optional[str]:
        return self.phones[0].normalized if self.phones else None
        
    @property
    def portfolio(self) -> Optional[str]:
        return self.portfolios[0] if self.portfolios else None

class Metadata(BaseModel):
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    processing_timestamp: str
    parser_version: str = "1.0.0"

class CandidateProfile(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None

class Experience(BaseModel):
    role: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    description: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list) # Canonical skill names
    evidence: Dict[str, str] = Field(default_factory=dict)

    @property
    def company_name(self) -> Optional[str]:
        return self.organization

    @property
    def job_title(self) -> Optional[str]:
        return self.role

    @property
    def dates(self) -> Optional[str]:
        if self.start_date and self.end_date:
            return f"{self.start_date} - {self.end_date}"
        return self.start_date or self.end_date

class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    grade: Optional[str] = None
    evidence: Dict[str, str] = Field(default_factory=dict)

    @property
    def university(self) -> Optional[str]:
        return self.institution

    @property
    def dates(self) -> Optional[str]:
        if self.start_date and self.end_date:
            return f"{self.start_date} - {self.end_date}"
        return self.start_date or self.end_date

class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    evidence: Dict[str, str] = Field(default_factory=dict)

class SkillMention(BaseModel):
    raw_text: str
    section: str
    match_type: str                 # "exact", "alias", "contextual"
    confidence: str                 # "high", "medium", "low"
    version: Optional[str] = None

class CanonicalSkill(BaseModel):
    canonical_name: str
    category: str
    mentions: List[SkillMention] = Field(default_factory=list)

class EntityMention(BaseModel):
    text: str
    section: str
    source: str
    is_current: Optional[bool] = None

class Entity(BaseModel):
    normalized_text: str
    label: str
    mentions: List[EntityMention] = Field(default_factory=list)

class ResumeData(BaseModel):
    metadata: Optional[Metadata] = None
    candidate: CandidateProfile = Field(default_factory=CandidateProfile)
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = None
    skills: List[CanonicalSkill] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    raw_text: str = ""
    cleaned_text: Optional[str] = None
    sections: List[Dict[str, Any]] = Field(default_factory=list)
