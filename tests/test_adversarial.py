import pytest
from resumind.parser import ResumeParser

@pytest.fixture
def parser():
    return ResumeParser()

def test_adversarial_contact_phone_collision(parser):
    text = "CGPA 8.3 / 10\nGraduation 2021-2025\nVersion 3.12.4"
    cleaned = parser.cleaner.clean(text)
    sections = parser.sectionizer.segment(cleaned)
    contact = parser.contact_extractor.extract(sections)
    
    # It should not extract random numbers as phone numbers
    assert len(contact.phones) == 0

def test_adversarial_skill_generic_word_collision(parser):
    text = "I would like to go further in my career and do my best."
    cleaned = parser.cleaner.clean(text)
    sections = parser.sectionizer.segment(cleaned)
    skills = parser.skill_extractor.extract(sections)
    
    # "go" should not be extracted as the "Go" programming language if it is lowercase in ordinary text, or at least we check if it is
    skill_names = [s.canonical_name for s in skills]
    assert "Go" not in skill_names

def test_adversarial_skill_exact_boundary(parser):
    # Ensure JavaScript does not accidentally match Java
    text = "SKILLS\nJavaScript Developer"
    cleaned = parser.cleaner.clean(text)
    sections = parser.sectionizer.segment(cleaned)
    skills = parser.skill_extractor.extract(sections)
    
    skill_names = [s.canonical_name for s in skills]
    assert "JavaScript" in skill_names
    assert "Java" not in skill_names

def test_adversarial_name_fallback_ignores_common_headers(parser):
    text = "CURRICULUM VITAE\nSoftware Engineer\nJohn Doe"
    cleaned = parser.cleaner.clean(text)
    sections = parser.sectionizer.segment(cleaned)
    contact = parser.contact_extractor.extract(sections)
    entities = parser.ner_extractor.extract(sections)
    resume = parser.assembler.assemble(text, cleaned, sections, contact, entities, [])
    assert resume.candidate.name != "CURRICULUM VITAE"
    assert resume.candidate.name != "RESUME"
    
def test_adversarial_ner_date_collision(parser):
    text = "EXPERIENCE\nMay 2025\nI may work on this project."
    cleaned = parser.cleaner.clean(text)
    sections = parser.sectionizer.segment(cleaned)
    entities = parser.ner_extractor.extract(sections)
    
def test_adversarial_section_spoofing(parser):
    text = "EXPERIENCE\nI worked on my projects alone.\n"
    cleaned = parser.cleaner.clean(text)
    sections = parser.sectionizer.segment(cleaned)
    assert len(sections) == 1
    assert "projects" not in [s.canonical_name for s in sections]
