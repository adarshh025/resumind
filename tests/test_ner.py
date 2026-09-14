import pytest
from resumind.nlp.ner import SemanticEntityExtractor
from resumind.segmentation.models import SectionBlock

def _make_section(name, lines):
    return SectionBlock(canonical_name=name, original_heading="", lines=lines, confidence=1.0)

def test_extract_candidate():
    extractor = SemanticEntityExtractor()
    sections = [
        _make_section("contact_header", [
            "Adarsh Aher",
            "Pune, India",
            "adarsh@example.com",
            "Software Engineer"
        ]),
        _make_section("experience", [
            "Software Engineer",
            "Google"
        ])
    ]
    
    entities = extractor.extract(sections)
    
    candidates = [e for e in entities if e.label == "CANDIDATE"]
    assert len(candidates) == 1
    assert candidates[0].normalized_text == "adarsh aher"
    assert candidates[0].mentions[0].section == "contact_header"

def test_extract_organizations_and_locations():
    extractor = SemanticEntityExtractor()
    sections = [
        _make_section("experience", [
            "Machine Learning Intern",
            "Worked at TechNova Inc.",
            "Jan 2025 - Present",
            "New York, USA"
        ]),
        _make_section("education", [
            "B.Tech CSE",
            "Studied at ABC Institute",
            "2024 - 2028",
            "Mumbai"
        ])
    ]
    
    entities = extractor.extract(sections)
    
    orgs = [e for e in entities if e.label == "ORGANIZATION"]
    assert len(orgs) >= 2
    
    org_texts = [o.normalized_text for o in orgs]
    assert "technova inc." in org_texts
    assert "abc institute" in org_texts
    
    locs = [e for e in entities if e.label == "LOCATION"]
    assert len(locs) >= 2
    loc_texts = [l.normalized_text for l in locs]
    assert "new york" in loc_texts
    assert "usa" in loc_texts

def test_extract_dates():
    extractor = SemanticEntityExtractor()
    sections = [
        _make_section("experience", [
            "Jan 2021 - Present",
            "05/2019 - 06/2020",
            "Graduated in 2018"
        ])
    ]
    
    entities = extractor.extract(sections)
    
    dates = [e for e in entities if e.label == "DATE"]
    date_mentions = [m for d in dates for m in d.mentions]
    
    assert any(m.text == "Jan 2021" and m.is_current is False for m in date_mentions)
    assert any(m.text.lower() == "present" and m.is_current is True for m in date_mentions)
    assert any(m.text == "05/2019" for m in date_mentions)
    assert any(m.text == "06/2020" for m in date_mentions)
    assert any(m.text == "2018" for m in date_mentions)

def test_entity_deduplication():
    extractor = SemanticEntityExtractor()
    sections = [
        _make_section("experience", [
            "Software Engineer at Google Inc.",
            "Software Engineer at Google Inc.",
        ]),
        _make_section("projects", [
            "Software Engineer at Google Inc."
        ])
    ]
    entities = extractor.extract(sections)
    orgs = [e for e in entities if e.label == "ORGANIZATION" and e.normalized_text == "google inc."]
    
    assert len(orgs) == 1
    # One mention for experience, one for projects
    assert len(orgs[0].mentions) == 2
