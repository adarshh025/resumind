import pytest
from resumind.assembly.assembler import ResumeAssembler
from resumind.models.resume import (
    ResumeData, Metadata, CandidateProfile, Experience, Education, Project,
    CanonicalSkill, Entity, EntityMention, ContactInfo
)
from resumind.segmentation.models import SectionBlock

def _make_section(name, lines):
    return SectionBlock(canonical_name=name, original_heading="", lines=lines, confidence=1.0)

def test_assemble_metadata():
    assembler = ResumeAssembler()
    resume = assembler.assemble(
        raw_text="",
        cleaned_text="",
        sections=[],
        contact_info=ContactInfo(),
        entities=[],
        skills=[],
        file_name="test_resume.pdf"
    )
    
    assert resume.metadata is not None
    assert resume.metadata.file_name == "test_resume.pdf"
    assert resume.metadata.file_type == "pdf"

def test_assemble_candidate():
    assembler = ResumeAssembler()
    
    # NLP fallback
    entities = [
        Entity(normalized_text="adarsh aher", label="CANDIDATE", mentions=[])
    ]
    
    resume = assembler.assemble(
        raw_text="",
        cleaned_text="",
        sections=[],
        contact_info=ContactInfo(),
        entities=entities,
        skills=[]
    )
    
    assert resume.candidate.name == "Adarsh Aher"

    # Aggressive fallback
    sections = [
        _make_section("contact_header", [
            "Jane Doe",
            "Software Engineer"
        ])
    ]
    resume2 = assembler.assemble(
        raw_text="",
        cleaned_text="",
        sections=sections,
        contact_info=ContactInfo(),
        entities=[],
        skills=[]
    )
    
    assert resume2.candidate.name == "Jane Doe"
    assert "Candidate name not found by NER. Extracting first valid line as fallback." in resume2.warnings

def test_assemble_experience():
    assembler = ResumeAssembler()
    sections = [
        _make_section("experience", [
            "TechNova Labs",
            "Machine Learning Intern",
            "Jan 2024 - Present",
            "- Built things",
            "- Used Python"
        ])
    ]
    
    entities = [
        Entity(normalized_text="technova labs", label="ORGANIZATION", mentions=[EntityMention(text="TechNova Labs", section="experience", source="test")]),
        Entity(normalized_text="jan 2024", label="DATE", mentions=[EntityMention(text="Jan 2024", section="experience", source="test")]),
        Entity(normalized_text="present", label="DATE", mentions=[EntityMention(text="Present", section="experience", source="test", is_current=True)])
    ]
    
    resume = assembler.assemble(
        raw_text="",
        cleaned_text="",
        sections=sections,
        contact_info=ContactInfo(),
        entities=entities,
        skills=[]
    )
    
    assert len(resume.experience) == 1
    exp = resume.experience[0]
    
    assert exp.organization == "Technova Labs"
    assert exp.role == "Machine Learning Intern"
    assert exp.start_date == "Jan 2024"
    assert exp.end_date == "Present"
    assert exp.is_current is True
    assert len(exp.description) == 2
    assert exp.description[0] == "Built things"
