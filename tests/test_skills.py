import pytest
from resumind.extraction.skills import SkillExtractor
from resumind.segmentation.models import SectionBlock

def _make_section(name, lines):
    return SectionBlock(canonical_name=name, original_heading="", lines=lines, confidence=1.0)

def test_extract_exact_and_alias():
    extractor = SkillExtractor()
    sections = [
        _make_section("skills", [
            "Python, Java, scikit-learn",
            "Familiar with js and react.js"
        ])
    ]
    skills = extractor.extract(sections)
    skill_names = {s.canonical_name for s in skills}
    
    assert "Python" in skill_names
    assert "Java" in skill_names
    assert "scikit-learn" in skill_names
    assert "JavaScript" in skill_names
    assert "React" in skill_names

def test_extract_versions():
    extractor = SkillExtractor()
    sections = [
        _make_section("experience", [
            "Developed backend using Python 3.12 and React 18."
        ])
    ]
    skills = extractor.extract(sections)
    
    python_skill = next((s for s in skills if s.canonical_name == "Python"), None)
    assert python_skill is not None
    assert python_skill.mentions[0].version == "3.12"
    
    react_skill = next((s for s in skills if s.canonical_name == "React"), None)
    assert react_skill is not None
    assert react_skill.mentions[0].version == "18"

def test_ambiguity_guard():
    extractor = SkillExtractor()
    
    # Negative test
    sections = [
        _make_section("summary", [
            "I want to Go to the next level."
        ])
    ]
    skills = extractor.extract(sections)
    assert not any(s.canonical_name == "Go" for s in skills)
    
    # Positive test
    sections = [
        _make_section("summary", [
            "Experience with Go and Python."
        ])
    ]
    skills = extractor.extract(sections)
    assert any(s.canonical_name == "Go" for s in skills)

def test_token_boundaries():
    extractor = SkillExtractor()
    sections = [
        _make_section("skills", [
            "C, C++, C#",
            "Google"
        ])
    ]
    skills = extractor.extract(sections)
    names = {s.canonical_name for s in skills}
    
    assert "C" in names
    assert "C++" in names
    assert "C#" in names
    assert "Go" not in names  # Should not extract 'Go' from 'Google'

def test_deduplication():
    extractor = SkillExtractor()
    sections = [
        _make_section("skills", [
            "Python"
        ]),
        _make_section("experience", [
            "Python"
        ])
    ]
    skills = extractor.extract(sections)
    python = next((s for s in skills if s.canonical_name == "Python"), None)
    
    assert python is not None
    # Deduplication across different sections should keep both mentions
    assert len(python.mentions) == 2
    
    # Deduplication within the same section exact text should merge
    sections = [
        _make_section("skills", [
            "Python",
            "Python"
        ])
    ]
    skills = extractor.extract(sections)
    python = next((s for s in skills if s.canonical_name == "Python"), None)
    assert len(python.mentions) == 1

def test_extract_soft_skills():
    extractor = SkillExtractor()
    sections = [
        _make_section("skills", [
            "Project Management, Agile, Scrum, Team Leadership",
            "Strong communication skills and problem-solving abilities."
        ])
    ]
    skills = extractor.extract(sections)
    names = {s.canonical_name for s in skills}
    
    assert "Project Management" in names
    assert "Agile" in names
    assert "Scrum" in names
    assert "Leadership" in names
    assert "Communication" in names
    assert "Problem Solving" in names

