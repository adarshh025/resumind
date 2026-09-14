import pytest
from resumind.parser import ResumeParser
from resumind.models.resume import ResumeData

def test_parser_instantiation():
    """Test that ResumeParser can be instantiated."""
    parser = ResumeParser()
    assert parser is not None

def test_parsefile_pdf(temp_pdf_file):
    """Test parsing a valid PDF extension."""
    parser = ResumeParser()
    result = parser.parsefile(temp_pdf_file)
    assert isinstance(result, dict)
    assert "contact" in result
    assert "skills" in result

def test_parsefile_docx(temp_docx_file):
    """Test parsing a valid DOCX extension."""
    parser = ResumeParser()
    result = parser.parsefile(temp_docx_file)
    assert isinstance(result, dict)

def test_parsefile_invalid_extension(tmp_path):
    """Test parsing an unsupported file format."""
    parser = ResumeParser()
    invalid_file = tmp_path / "resume.txt"
    invalid_file.write_text("dummy text")
    
    with pytest.raises(ValueError, match="Unsupported file format"):
        parser.parsefile(str(invalid_file))

def test_parsefile_not_found():
    """Test parsing a non-existent file."""
    parser = ResumeParser()
    with pytest.raises(FileNotFoundError):
        parser.parsefile("non_existent_file.pdf")
