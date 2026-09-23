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


def test_adversarial_candidate_name_safeguards(parser):
    """Ensure table borders, divider lines, and raw job titles are never extracted as names."""
    adversarial_inputs = [
        "|---|---|",
        "====================",
        "--------------------",
        "---------------~----",
        "+------------------+",
        "Cloud Solutions Architect",
        "Data Analyst",
        "Senior Software Engineer",
        "jane.doe@example.com | +1-555-0199",
        "https://linkedin.com/in/janedoe"
    ]
    for adv in adversarial_inputs:
        text = f"{adv}\nEXPERIENCE\nSoftware Engineer at TechCorp"
        cleaned = parser.cleaner.clean(text)
        sections = parser.sectionizer.segment(cleaned)
        entities = parser.ner_extractor.extract(sections)
        contact = parser.contact_extractor.extract(sections)
        resume = parser.assembler.assemble(text, cleaned, sections, contact, entities, [])
        assert resume.candidate.name != adv, f"Failed safeguard: '{adv}' was extracted as candidate name."


def test_adversarial_contact_pipe_name_extraction(parser):
    """Ensure candidate name is cleanly extracted when embedded in a pipe-separated contact line."""
    text = "David Chen | dchen@example.com | (555) 123-4567 | San Francisco, CA\nSUMMARY\nSoftware Engineer"
    cleaned = parser.cleaner.clean(text)
    sections = parser.sectionizer.segment(cleaned)
    entities = parser.ner_extractor.extract(sections)
    contact = parser.contact_extractor.extract(sections)
    resume = parser.assembler.assemble(text, cleaned, sections, contact, entities, [])
    assert resume.candidate.name == "David Chen"
    assert "dchen@example.com" in resume.contact.emails


def test_adversarial_inline_section_headings(parser):
    """Ensure inline section headings with colons or dashes are properly segmented."""
    text = (
        "John Smith\n"
        "Experience: Principal Engineer at TechCorp\n"
        "- Architected distributed data pipelines.\n"
        "Education: B.S. Computer Science - Stanford University\n"
        "Skills: Python, Go, Docker, Kubernetes\n"
    )
    cleaned = parser.cleaner.clean(text)
    sections = parser.sectionizer.segment(cleaned)
    sec_names = [s.canonical_name for s in sections]
    assert "experience" in sec_names
    assert "education" in sec_names
    assert "skills" in sec_names

    exp_sec = next(s for s in sections if s.canonical_name == "experience")
    assert any("Principal Engineer at TechCorp" in line for line in exp_sec.lines)


def test_adversarial_experience_one_line_patterns(parser):
    """Ensure single-line role and organization patterns extract both role and organization."""
    patterns = [
        ("Senior Software Engineer at Google", "Senior Software Engineer", "Google"),
        ("Google - Senior Software Engineer", "Senior Software Engineer", "Google"),
        ("Senior Software Engineer | Google", "Senior Software Engineer", "Google"),
        ("Google | Senior Software Engineer", "Senior Software Engineer", "Google"),
        ("ML Engineer @ OpenAI", "ML Engineer", "Openai"),
        ("Operations Manager | Apex Logistics | Chicago, IL | Jan 2021 – Present", "Operations Manager", "Apex Logistics")
    ]
    for line, exp_role, exp_org in patterns:
        text = f"Jane Doe\nEXPERIENCE\n{line}\n- Led team initiatives."
        cleaned = parser.cleaner.clean(text)
        sections = parser.sectionizer.segment(cleaned)
        entities = parser.ner_extractor.extract(sections)
        contact = parser.contact_extractor.extract(sections)
        resume = parser.assembler.assemble(text, cleaned, sections, contact, entities, [])
        assert len(resume.experience) >= 1
        found_exp = resume.experience[0]
        assert found_exp.role.lower() == exp_role.lower(), f"Expected role {exp_role}, got {found_exp.role} for {line}"
        assert found_exp.organization.lower() == exp_org.lower(), f"Expected org {exp_org}, got {found_exp.organization} for {line}"


def test_adversarial_education_one_line_patterns(parser):
    """Ensure single-line degree and university patterns extract both degree and institution."""
    patterns = [
        ("B.Sc in Computer Science - Stanford University", "B.Sc in Computer Science", "Stanford University"),
        ("Bachelor of Business Administration | University of Illinois | May 2017", "Bachelor of Business Administration", "University of Illinois"),
        ("B.S. Marketing, Florida State University, 2015", "B.S. Marketing", "Florida State University")
    ]
    for line, exp_deg, exp_inst in patterns:
        text = f"Jane Doe\nEDUCATION\n{line}\n"
        cleaned = parser.cleaner.clean(text)
        sections = parser.sectionizer.segment(cleaned)
        entities = parser.ner_extractor.extract(sections)
        contact = parser.contact_extractor.extract(sections)
        resume = parser.assembler.assemble(text, cleaned, sections, contact, entities, [])
        assert len(resume.education) >= 1
        found_edu = resume.education[0]
        assert found_edu.degree.lower() == exp_deg.lower(), f"Expected degree {exp_deg}, got {found_edu.degree} for {line}"
        assert found_edu.institution.lower() == exp_inst.lower(), f"Expected inst {exp_inst}, got {found_edu.institution} for {line}"


def test_adversarial_new_skills_ontology(parser):
    """Verify newly added technical skills with aliases and ambiguity protection."""
    text = "SKILLS\nHTML5, CSS3, Bash, RESTful API, GraphQL, CI/CD, Kafka, Jenkins\n"
    cleaned = parser.cleaner.clean(text)
    sections = parser.sectionizer.segment(cleaned)
    skills = parser.skill_extractor.extract(sections)
    skill_names = {s.canonical_name for s in skills}
    expected = {"HTML", "CSS", "Bash", "REST API", "GraphQL", "CI/CD", "Kafka", "Jenkins"}
    assert expected.issubset(skill_names), f"Missing skills: {expected - skill_names}"

    # Ambiguity check: 'in a nutshell' outside technical context should NOT match Bash/shell
    summary_text = "SUMMARY\nIn a nutshell, I am an enthusiastic professional looking for opportunities.\n"
    summary_cleaned = parser.cleaner.clean(summary_text)
    summary_sections = parser.sectionizer.segment(summary_cleaned)
    summary_skills = parser.skill_extractor.extract(summary_sections)
    summary_skill_names = {s.canonical_name for s in summary_skills}
    assert "Bash" not in summary_skill_names

