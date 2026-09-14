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
    
    # 2. Skill Extraction Benchmark
    skill_text = """
    SKILLS
    Languages: Python, Java, C++, JS
    Web: React, FastAPI, HTML
    Data: sklearn, pandas
    """
    
    cleaned_lines2 = parser.cleaner.clean(skill_text)
    sections2 = parser.sectionizer.segment(cleaned_lines2)
    skills = parser.skill_extractor.extract(sections2)
    
    print("\nSkill Extraction (Resolved Aliases):")
    for s in skills:
        print(f" - {s.canonical_name} (from '{s.mentions[0].raw_text}')")
        
    # 3. Assembly test
    print("\nBenchmarking complete.")

if __name__ == "__main__":
    run_evaluation()
