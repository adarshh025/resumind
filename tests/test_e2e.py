import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from resumind.parser import ResumeParser
from resumind.ingestion.models import DocumentExtractionResult

@patch("resumind.parser.get_extractor")
def test_full_pipeline_e2e(mock_get_extractor, tmp_path):
    parser = ResumeParser()
    
    # Mock extractor output
    mock_extractor = MagicMock()
    test_file = tmp_path / "synthetic_resume.txt"
    test_file.write_text("""
John Doe
Software Engineer
San Francisco, CA
johndoe@email.com
github.com/johndoe
linkedin.com/in/johndoe

SUMMARY
Experienced software engineer with a passion for building scalable systems.

SKILLS
Python, Java, React, SQL

EXPERIENCE
TechCorp
Senior Developer
01/2020 - Present
- Designed microservices in Python.
- Built a web dashboard using React.

EDUCATION
B.Sc Computer Science
University of Technology
2015 - 2019
""", encoding="utf-8")

    mock_extractor.extract.return_value = DocumentExtractionResult(
        filename="synthetic_resume.txt",
        source_format="txt",
        status="SUCCESS",
        raw_text=test_file.read_text(encoding="utf-8"),
        metadata={},
        warnings=[]
    )
    mock_get_extractor.return_value = mock_extractor

    resume_data = parser.parsefile(str(test_file))
    
    # Assert unified payload structure
    assert "metadata" in resume_data
    assert resume_data["metadata"]["file_name"] == "synthetic_resume.txt"
    
    # Candidate
    assert resume_data["candidate"]["name"] == "John Doe"
    
    # Contacts
    assert "johndoe@email.com" in resume_data["contact"]["emails"]
    assert any("github.com" in url for url in resume_data["contact"]["github"])
    
    # Summary
    assert "Experienced software engineer" in resume_data["summary"]
    
    # Skills
    skills = [s["canonical_name"] for s in resume_data["skills"]]
    assert "Python" in skills
    assert "Java" in skills
    assert "React" in skills
    
    # Experience
    assert len(resume_data["experience"]) == 1
    exp = resume_data["experience"][0]
    assert exp["organization"] == "Techcorp"
    assert exp["role"] == "Senior Developer"
    assert exp["start_date"] == "01/2020"
    assert exp["is_current"] is True
    assert "Python" in exp["skills"]
    assert "React" in exp["skills"]
    assert "Designed microservices" in exp["description"][0]
    
    # Education
    assert len(resume_data["education"]) == 1
    edu = resume_data["education"][0]
    assert edu["institution"] == "University Of Technology"
    assert edu["degree"] == "B.Sc Computer Science"
    assert edu["start_date"] == "2015"
    assert edu["end_date"] == "2019"
