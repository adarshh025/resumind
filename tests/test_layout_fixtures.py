from pathlib import Path
import pytest
from resumind.parser import ResumeParser
from resumind.models.resume import ResumeData

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "generated_resumes"
LAYOUT_FILES = sorted(FIXTURES_DIR.glob("*.pdf"))


def test_layout_fixtures_count():
    """Verify that the repository contains the required 10-20 layout benchmark fixtures."""
    assert len(LAYOUT_FILES) >= 10, f"Expected at least 10 layout fixtures, found {len(LAYOUT_FILES)}"
    assert len(LAYOUT_FILES) == 20, f"Expected 20 layout fixtures, found {len(LAYOUT_FILES)}"


@pytest.mark.parametrize("pdf_path", LAYOUT_FILES, ids=[f.name for f in LAYOUT_FILES])
def test_parse_layout_fixture(pdf_path: Path):
    """
    Stress-test the parser against diverse real-world and synthetic resume layouts.
    Validates structural integrity, Pydantic schema compliance, and crash-resilience
    without making invalid assumptions about sparse or missing fields.
    """
    parser = ResumeParser()
    
    # 1. Ensure parser executes without unhandled exceptions
    try:
        result = parser.parsefile(str(pdf_path))
    except Exception as exc:
        pytest.fail(f"Parser failed on layout fixture '{pdf_path.name}' with exception: {exc}")

    # 2. Structural & Dictionary Validation
    assert isinstance(result, dict), f"Fixture '{pdf_path.name}' did not return a dictionary."
    
    # 3. Required top-level keys
    required_keys = {
        "metadata", "candidate", "contact", "summary", "skills",
        "education", "experience", "projects", "entities", "warnings",
        "raw_text", "cleaned_text", "sections"
    }
    missing_keys = required_keys - set(result.keys())
    assert not missing_keys, f"Fixture '{pdf_path.name}' missing required schema keys: {missing_keys}"

    # 4. Metadata verification
    assert result["metadata"] is not None
    assert result["metadata"]["file_name"] == pdf_path.name
    assert result["metadata"]["file_type"] == "pdf"

    # 5. Extraction content verification (all 20 generated layouts contain text)
    assert len(result["raw_text"]) > 0, f"Fixture '{pdf_path.name}' yielded empty raw_text"
    assert len(result["sections"]) > 0, f"Fixture '{pdf_path.name}' yielded no segmented sections"

    # 6. Strict Pydantic Schema Validation (ensures data types & structure conform exactly)
    validated = ResumeData.model_validate(result)
    assert validated.metadata.file_name == pdf_path.name

    # 7. Semantic Quality Checks across all fixtures
    # Candidate name must be a plausible human name (not markdown borders, table cells, or job titles)
    cand_name = result.get("candidate", {}).get("name")
    assert cand_name is not None, f"Fixture '{pdf_path.name}' failed to extract candidate name"
    assert "|---|" not in cand_name
    assert "===" not in cand_name
    assert "---" not in cand_name
    assert "@" not in cand_name


def test_semantic_fixture_1_chronological():
    parser = ResumeParser()
    path = FIXTURES_DIR / "1._traditional_single-column.pdf"
    result = parser.parsefile(str(path))

    assert result["candidate"]["name"] == "Robert Vance"
    assert "r.vance@email.com" in result["contact"]["emails"]

    # Experience semantic validation
    roles = [e["role"] for e in result["experience"] if e.get("role")]
    orgs = [e["organization"] for e in result["experience"] if e.get("organization")]
    assert any("Operations Manager" in r for r in roles)
    assert any("Apex Logistics" in o for o in orgs)
    assert any("Logistics Coordinator" in r for r in roles)

    # Education semantic validation
    assert len(result["education"]) >= 1
    edu = result["education"][0]
    assert "Bachelor of Business Administration" in edu["degree"]
    assert "University Of Illinois" in edu["institution"]


def test_semantic_fixture_2_twocolumn():
    parser = ResumeParser()
    path = FIXTURES_DIR / "2._two-column.pdf"
    result = parser.parsefile(str(path))

    assert result["candidate"]["name"] == "Elena Rostova"
    assert "elena.r@email.com" in result["contact"]["emails"]
    roles = [e["role"] for e in result["experience"] if e.get("role")]
    assert any("Senior Designer" in r for r in roles)


def test_semantic_fixture_4_dense_technical():
    parser = ResumeParser()
    path = FIXTURES_DIR / "4._dense_technical_resume.pdf"
    result = parser.parsefile(str(path))

    assert result["candidate"]["name"] == "Priya Patel"
    roles = [e["role"] for e in result["experience"] if e.get("role")]
    assert any("Principal Cloud Engineer" in r for r in roles)
    skill_names = {s["canonical_name"] for s in result["skills"]}
    assert {"AWS", "Docker", "Kubernetes", "Python"}.issubset(skill_names)


def test_semantic_fixture_7_no_summary():
    parser = ResumeParser()
    path = FIXTURES_DIR / "7._resume_with_no_summary.pdf"
    result = parser.parsefile(str(path))

    assert result["candidate"]["name"] == "Michael O'Connor"
    roles = [e["role"] for e in result["experience"] if e.get("role")]
    assert any("Regional Sales Director" in r for r in roles)
    assert len(result["education"]) >= 1
    assert "B.S. Marketing" in result["education"][0]["degree"]
    assert "Florida State University" in result["education"][0]["institution"]


def test_semantic_fixture_8_no_projects():
    parser = ResumeParser()
    path = FIXTURES_DIR / "8._resume_with_no_projects.pdf"
    result = parser.parsefile(str(path))

    assert result["candidate"]["name"] == "Linda Kravitz"
    roles = [e["role"] for e in result["experience"] if e.get("role")]
    assert any("HR Director" in r for r in roles)
    degs = [d["degree"] for d in result["education"] if d.get("degree")]
    assert any("M.S. Human Resource Management" in d for d in degs)
    assert any("B.A. Psychology" in d for d in degs)


def test_semantic_fixture_11_aliases():
    parser = ResumeParser()
    path = FIXTURES_DIR / "11._resume_with_aliases.pdf"
    result = parser.parsefile(str(path))

    assert result["candidate"]["name"] == "Jordan Lee"
    skill_names = {s["canonical_name"] for s in result["skills"]}
    assert "React" in skill_names
    assert "Python" in skill_names
    assert "scikit-learn" in skill_names


def test_semantic_fixture_17_education_first():
    parser = ResumeParser()
    path = FIXTURES_DIR / "17._resume_with_education_first.pdf"
    result = parser.parsefile(str(path))

    assert result["candidate"]["name"] == "Dr. Emily Carter"
    degs = [d["degree"] for d in result["education"] if d.get("degree")]
    assert any("Ph.D. in Computational Biology" in d for d in degs)
    assert any("M.S. in Bioinformatics" in d for d in degs)

