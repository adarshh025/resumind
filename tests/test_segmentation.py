import pytest
from resumind.segmentation.sectionizer import Sectionizer

def test_sectionizer_basic():
    sectionizer = Sectionizer()
    lines = [
        "Adarsh Aher",
        "aheradarsh6@gmail.com",
        "",
        "PROFESSIONAL SUMMARY",
        "A software engineer.",
        "",
        "EXPERIENCE",
        "Company A",
        "Company B",
        "",
        "EDUCATION",
        "B.Tech",
        "",
        "SKILLS",
        "Python, Java"
    ]
    
    sections = sectionizer.segment(lines)
    
    # We expect 5 sections: contact_header, summary, experience, education, skills
    assert len(sections) == 5
    assert sections[0].canonical_name == "contact_header"
    assert "Adarsh Aher" in sections[0].lines
    
    assert sections[1].canonical_name == "summary"
    assert sections[1].original_heading == "PROFESSIONAL SUMMARY"
    
    assert sections[2].canonical_name == "experience"
    assert sections[2].original_heading == "EXPERIENCE"
    assert "Company A" in sections[2].lines
    
    assert sections[3].canonical_name == "education"
    assert sections[4].canonical_name == "skills"

def test_sectionizer_aliases():
    sectionizer = Sectionizer()
    lines = [
        "WORK HISTORY",
        "Company A",
        "ACADEMIC BACKGROUND",
        "B.Tech"
    ]
    sections = sectionizer.segment(lines)
    
    assert len(sections) == 2
    assert sections[0].canonical_name == "experience"
    assert sections[1].canonical_name == "education"

def test_sectionizer_unknown_sections():
    sectionizer = Sectionizer()
    lines = [
        "AWARDS AND HONORS",
        "Best Student Award",
        "PROJECTS",
        "My Project"
    ]
    sections = sectionizer.segment(lines)
    assert len(sections) == 2
    assert sections[0].canonical_name == "unknown"
    assert sections[0].original_heading == "AWARDS AND HONORS"
    assert sections[1].canonical_name == "projects"
    
def test_sectionizer_false_positives():
    sectionizer = Sectionizer()
    lines = [
        "EXPERIENCE",
        "Software Engineer",
        "I used many skills here."
    ]
    sections = sectionizer.segment(lines)
    assert len(sections) == 1
    assert sections[0].canonical_name == "experience"
    
def test_sectionizer_duplicate_sections():
    sectionizer = Sectionizer()
    lines = [
        "PROJECTS",
        "Proj 1",
        "PROJECTS",
        "Proj 2"
    ]
    sections = sectionizer.segment(lines)
    assert len(sections) == 2
    assert sections[0].canonical_name == "projects"
    assert "Proj 1" in sections[0].lines
    assert sections[1].canonical_name == "projects"
    assert "Proj 2" in sections[1].lines

def test_sectionizer_inline_headings():
    sectionizer = Sectionizer()
    lines = [
        "Jane Doe",
        "Experience: Principal Engineer at Google",
        "- Built backend microservices in Go",
        "Education: B.S. Computer Science - Stanford University",
        "Skills: Python, SQL, Machine Learning",
        "Core Technologies: AWS, GCP, Docker"
    ]
    sections = sectionizer.segment(lines)
    names = [s.canonical_name for s in sections]
    assert names == ["contact_header", "experience", "education", "skills", "skills"]
    assert "Principal Engineer at Google" in sections[1].lines
    assert "B.S. Computer Science - Stanford University" in sections[2].lines
    assert "Python, SQL, Machine Learning" in sections[3].lines

def test_sectionizer_inline_heading_false_positives():
    sectionizer = Sectionizer()
    lines = [
        "SUMMARY",
        "I have 5 years of experience with Python and SQL in production.",
        "Passionate about applying skills to real-world challenges."
    ]
    sections = sectionizer.segment(lines)
    assert len(sections) == 1
    assert sections[0].canonical_name == "summary"
    assert "I have 5 years of experience with Python and SQL in production." in sections[0].lines

