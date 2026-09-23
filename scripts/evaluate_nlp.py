import os
import json
from pathlib import Path
from resumind.parser import ResumeParser
from resumind.models.resume import ResumeData

def run_evaluation():
    parser = ResumeParser()
    
    # 1. Contact Extraction Benchmark
    contact_text = """
    Jane Doe
    Software Engineer
    jane.doe.test@gmail.com
    +1 (555) 123-4567
    linkedin.com/in/janedoe
    github.com/janedoe
    """
    
    cleaned_lines = parser.cleaner.clean(contact_text)
    sections = parser.sectionizer.segment(cleaned_lines)
    contact_info = parser.contact_extractor.extract(sections)
    
    print("Contact Extraction:")
    print("Emails:", contact_info.emails)
    print("Phones:", [p.normalized for p in contact_info.phones])
    print("LinkedIn:", contact_info.linkedin)
    print("GitHub:", contact_info.github)
    
    # 2. Skill Extraction Benchmark (Technical)
    skill_text = """
    SKILLS
    Languages: Python, Java, C++, JS
    Web: React, FastAPI, HTML
    Data: sklearn, pandas
    """
    
    cleaned_lines2 = parser.cleaner.clean(skill_text)
    sections2 = parser.sectionizer.segment(cleaned_lines2)
    skills = parser.skill_extractor.extract(sections2)
    
    print("\nSkill Extraction (Technical & Resolved Aliases):")
    for s in skills:
        print(f" - {s.canonical_name} (from '{s.mentions[0].raw_text}')")
        
    tech_names = {s.canonical_name for s in skills}
    assert "Python" in tech_names
    assert "JavaScript" in tech_names
    assert "scikit-learn" in tech_names
    assert "React" in tech_names
    print("Technical skill extraction: PASS")

    # 3. Soft Skills & Methodologies Benchmark
    soft_skill_text = """
    SKILLS
    Methodologies: Agile, Scrum, Project Management (PMP)
    Soft Skills: Team Leadership, Written Communication, Cross-Functional Teamwork, Problem-Solving
    """
    cleaned_lines3 = parser.cleaner.clean(soft_skill_text)
    sections3 = parser.sectionizer.segment(cleaned_lines3)
    soft_skills = parser.skill_extractor.extract(sections3)
    
    print("\nSkill Extraction (Soft Skills & Methodologies):")
    for s in soft_skills:
        print(f" - {s.canonical_name} (from '{s.mentions[0].raw_text}')")
        
    soft_names = {s.canonical_name for s in soft_skills}
    assert "Project Management" in soft_names, "Project Management not extracted"
    assert "Leadership" in soft_names, "Leadership not extracted"
    assert "Communication" in soft_names, "Communication not extracted"
    assert "Teamwork" in soft_names, "Teamwork not extracted"
    assert "Problem Solving" in soft_names, "Problem Solving not extracted"
    assert "Agile" in soft_names, "Agile not extracted"
    assert "Scrum" in soft_names, "Scrum not extracted"
    print("Soft skills extraction: PASS")

    # 4. Ambiguity Protection Verification
    generic_text = """
    SUMMARY
    I lead initiatives to drive performance and go the extra mile.
    """
    cleaned_lines4 = parser.cleaner.clean(generic_text)
    sections4 = parser.sectionizer.segment(cleaned_lines4)
    generic_skills = parser.skill_extractor.extract(sections4)
    ambiguous_names = {s.canonical_name for s in generic_skills}
    assert "Go" not in ambiguous_names, "Generic 'go' incorrectly matched as Go language"
    assert len(generic_skills) == 0, f"Unexpected skills from generic text: {ambiguous_names}"
    print("Ambiguity protection: PASS")

    print("\nAll NLP evaluation benchmarks passed successfully.")

if __name__ == "__main__":
    run_evaluation()

