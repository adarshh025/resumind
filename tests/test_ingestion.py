import pytest
from pathlib import Path

from resumind.ingestion.base import detect_file_format, validate_filepath
from resumind.ingestion.pdf import PdfExtractor
from resumind.ingestion.docx import DocxExtractor
from resumind.ingestion.factory import get_extractor
from resumind.parser import ResumeParser

FIXTURE_DIR = Path(__file__).parent / "fixtures"

def test_validate_filepath(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_filepath(Path("non_existent_file.pdf"))
        
    with pytest.raises(ValueError, match="not a valid file"):
        validate_filepath(FIXTURE_DIR) # directory
        
    no_ext = tmp_path / "noext"
    no_ext.touch()
    with pytest.raises(ValueError, match="no extension"):
        validate_filepath(no_ext)

def test_detect_file_format():
    assert detect_file_format(Path("test.pdf")) == "pdf"
    assert detect_file_format(Path("test.docx")) == "docx"
    with pytest.raises(ValueError, match="Unsupported file format"):
        detect_file_format(Path("test.txt"))

def test_pdf_extractor_valid():
    extractor = PdfExtractor()
    result = extractor.extract(FIXTURE_DIR / "fixture_a.pdf")
    
    assert result.status == "SUCCESS"
    assert result.page_count == 1
    assert "Adarsh Aher" in result.raw_text
    assert "Software Engineer" in result.raw_text

def test_pdf_extractor_multipage():
    extractor = PdfExtractor()
    result = extractor.extract(FIXTURE_DIR / "fixture_b.pdf")
    
    assert result.status == "SUCCESS"
    assert result.page_count == 2
    assert "Page 1" in result.raw_text
    assert "Page 2" in result.raw_text

def test_pdf_extractor_empty():
    extractor = PdfExtractor()
    result = extractor.extract(FIXTURE_DIR / "fixture_empty.pdf")
    
    # fpdf might add some minimal text or none. If none, it should be TEXT_NOT_EXTRACTABLE
    if result.status == "SUCCESS":
        assert not result.raw_text.strip()
    else:
        assert result.status == "TEXT_NOT_EXTRACTABLE"

def test_pdf_extractor_corrupt():
    extractor = PdfExtractor()
    result = extractor.extract(FIXTURE_DIR / "corrupt.pdf")
    
    assert result.status == "ERROR"
    assert "PDF Syntax Error" in result.errors[0]

def test_docx_extractor_valid():
    extractor = DocxExtractor()
    result = extractor.extract(FIXTURE_DIR / "fixture_a.docx")
    
    assert result.status == "SUCCESS"
    assert "Adarsh Aher" in result.raw_text
    assert "Software Engineer" in result.raw_text

def test_docx_extractor_tables():
    extractor = DocxExtractor()
    result = extractor.extract(FIXTURE_DIR / "fixture_c.docx")
    
    assert result.status == "SUCCESS"
    assert "Python | Expert" in result.raw_text
    assert "FastAPI | Advanced" in result.raw_text

def test_docx_extractor_corrupt():
    extractor = DocxExtractor()
    result = extractor.extract(FIXTURE_DIR / "corrupt.docx")
    
    assert result.status == "ERROR"
    assert "not a zip file" in result.errors[0].lower() or "invalid" in result.errors[0].lower()

def test_factory():
    assert isinstance(get_extractor(FIXTURE_DIR / "fixture_a.pdf"), PdfExtractor)
    assert isinstance(get_extractor(FIXTURE_DIR / "fixture_a.docx"), DocxExtractor)

def test_parser_integration():
    parser = ResumeParser()
    result = parser.parsefile(str(FIXTURE_DIR / "fixture_a.pdf"))
    
    assert isinstance(result, dict)
    assert "raw_text" in result
    assert "Adarsh Aher" in result["raw_text"]
