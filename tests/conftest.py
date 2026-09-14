import pytest
import os
import tempfile

@pytest.fixture
def temp_pdf_file():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4\n")
        temp_path = f.name
    yield temp_path
    os.remove(temp_path)

@pytest.fixture
def temp_docx_file():
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        f.write(b"PK\x03\x04\n")
        temp_path = f.name
    yield temp_path
    os.remove(temp_path)
