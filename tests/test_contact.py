import pytest
from resumind.extraction.contact import ContactExtractor
from resumind.segmentation.models import SectionBlock

def _make_section(lines):
    return [SectionBlock(canonical_name="contact_header", original_heading="", lines=lines, confidence=1.0)]

def test_extract_emails():
    extractor = ContactExtractor()
    lines = [
        "adarsh@example.com",
        "Contact me at First.Last+tag@Sub.Domain.co.in.",
        "adarsh@example.com", # duplicate
        "not.an.email@"
    ]
    contact = extractor.extract(_make_section(lines))
    assert len(contact.emails) == 2
    assert contact.emails[0] == "adarsh@example.com"
    assert contact.emails[1] == "first.last+tag@sub.domain.co.in"

def test_extract_phones_valid():
    extractor = ContactExtractor()
    lines = [
        "+91 9876543210",
        "+1 (415) 555-0123",
        "09876543210",
        "987-654-3210"
    ]
    contact = extractor.extract(_make_section(lines))
    assert len(contact.phones) == 4
    assert contact.phones[0].normalized == "+919876543210"
    assert contact.phones[1].normalized == "+14155550123"
    assert contact.phones[2].normalized == "09876543210"
    assert contact.phones[3].normalized == "9876543210"

def test_extract_phones_false_positives():
    extractor = ContactExtractor()
    lines = [
        "GPA 3.8 / 4.0",
        "Years 2021-2025",
        "Years 05/2021 - 06/2025",
        "Date 12-05-2024",
        "Total 100%",
        "Version 3.10.4",
        "ID 0000000000"
    ]
    contact = extractor.extract(_make_section(lines))
    assert len(contact.phones) == 0

def test_extract_urls():
    extractor = ContactExtractor()
    lines = [
        "https://www.linkedin.com/in/username",
        "linkedin.com/in/username2",
        "github.com/username",
        "https://portfolio.dev",
        "linkedin.com/company/resumind",
        "myblog.tech",
        "version 3.12.4"
    ]
    contact = extractor.extract(_make_section(lines))
    
    assert len(contact.linkedin) == 2
    assert contact.linkedin[0] == "https://www.linkedin.com/in/username"
    assert contact.linkedin[1] == "https://linkedin.com/in/username2"
    
    assert len(contact.github) == 1
    assert contact.github[0] == "https://github.com/username"
    
    assert len(contact.portfolios) == 2
    assert "https://portfolio.dev" in contact.portfolios
    assert "https://myblog.tech" in contact.portfolios
    
    assert len(contact.other_urls) == 1
    assert contact.other_urls[0] == "https://linkedin.com/company/resumind"

def test_contact_deduplication():
    extractor = ContactExtractor()
    lines = [
        "+91 98765 43210",
        "+91-9876543210", # same normalized
        "https://GITHUB.COM/username",
        "github.com/username" # same normalized
    ]
    contact = extractor.extract(_make_section(lines))
    
    assert len(contact.phones) == 1
    assert len(contact.github) == 1
