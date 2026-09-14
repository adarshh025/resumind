import pytest
from resumind.preprocessing.cleaner import ResumeCleaner

def test_cleaner_whitespace():
    cleaner = ResumeCleaner()
    raw = "John    Doe \n  Software  Engineer  "
    cleaned = cleaner.clean(raw)
    assert cleaned == ["John Doe", "Software Engineer"]

def test_cleaner_bullets():
    cleaner = ResumeCleaner()
    raw = "• Python\n◦ Java\n► C++\n- SQL\n* Bash"
    cleaned = cleaner.clean(raw)
    assert cleaned == ["- Python", "- Java", "- C++", "- SQL", "- Bash"]

def test_cleaner_page_markers():
    cleaner = ResumeCleaner()
    raw = "Page 1\nExperience\nPage 2 of 3\nEducation\n1 / 2\nSkills"
    cleaned = cleaner.clean(raw)
    assert cleaned == ["Experience", "Education", "Skills"]

def test_cleaner_control_chars():
    cleaner = ResumeCleaner()
    raw = "Hello\x00World\nTest\x0b"
    cleaned = cleaner.clean(raw)
    assert cleaned == ["HelloWorld", "Test"]

def test_cleaner_preserves_blank_lines():
    cleaner = ResumeCleaner()
    raw = "Experience\n\nCompany A"
    cleaned = cleaner.clean(raw)
    assert cleaned == ["Experience", "", "Company A"]
