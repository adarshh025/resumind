import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pathlib import Path
from resumind.app.main import app
from resumind.ingestion.models import DocumentExtractionResult

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_unsupported_file(tmp_path):
    test_file = tmp_path / "resume.xyz"
    test_file.write_text("dummy")
    
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/resumes/parse",
            files={"file": ("resume.xyz", f, "text/plain")}
        )
    
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"

def test_upload_empty_file(tmp_path):
    test_file = tmp_path / "empty.pdf"
    test_file.touch()
    
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/resumes/parse",
            files={"file": ("empty.pdf", f, "application/pdf")}
        )
    
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_DOCUMENT"

@patch("resumind.parser.get_extractor")
def test_upload_valid_synthetic_file(mock_get_extractor, tmp_path):
    test_file = tmp_path / "valid.pdf"
    content = """
John Doe
Software Engineer
johndoe@email.com

SKILLS
Python, FastAPI, SQL
"""
    test_file.write_bytes(content.encode("utf-8"))

    # Mock the extractor behavior
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = DocumentExtractionResult(
        filename="valid.pdf",
        source_format="pdf",
        status="SUCCESS",
        raw_text=content,
        metadata={},
        warnings=[]
    )
    mock_get_extractor.return_value = mock_extractor

    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/resumes/parse",
            files={"file": ("valid.pdf", f, "application/pdf")}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "resume" in data
    resume = data["resume"]
    assert resume["candidate"]["name"] == "John Doe"
    assert "johndoe@email.com" in resume["contact"]["emails"]
    
    skills = [s["canonical_name"] for s in resume["skills"]]
    assert "Python" in skills

def test_upload_oversized_file(tmp_path):
    test_file = tmp_path / "oversized.pdf"
    # Create file slightly larger than 5 MB
    test_file.write_bytes(b"A" * (5 * 1024 * 1024 + 1024))
    
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/resumes/parse",
            files={"file": ("oversized.pdf", f, "application/pdf")}
        )
    
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"

@patch("resumind.parser.get_extractor")
def test_upload_valid_docx_file(mock_get_extractor, tmp_path):
    test_file = tmp_path / "valid.docx"
    content = "Jane Doe\nProject Manager\njane@example.com\n\nSKILLS\nAgile, Scrum"
    test_file.write_bytes(content.encode("utf-8"))

    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = DocumentExtractionResult(
        filename="valid.docx",
        source_format="docx",
        status="SUCCESS",
        raw_text=content,
        metadata={},
        warnings=[]
    )
    mock_get_extractor.return_value = mock_extractor

    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/resumes/parse",
            files={"file": ("valid.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["resume"]["candidate"]["name"] == "Jane Doe"
    assert "Project Management" not in data["resume"]["skills"]  # title is manager
    skills = [s["canonical_name"] for s in data["resume"]["skills"]]
    assert "Agile" in skills
    assert "Scrum" in skills

