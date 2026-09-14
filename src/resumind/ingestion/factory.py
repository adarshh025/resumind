from pathlib import Path

from resumind.ingestion.base import DocumentExtractor, detect_file_format, validate_filepath
from resumind.ingestion.pdf import PdfExtractor
from resumind.ingestion.docx import DocxExtractor

def get_extractor(filepath: Path) -> DocumentExtractor:
    """
    Returns the appropriate extractor based on the file format.
    
    Args:
        filepath (Path): The file path.
        
    Returns:
        DocumentExtractor: The format-specific extractor.
    """
    validate_filepath(filepath)
    fmt = detect_file_format(filepath)
    
    if fmt == "pdf":
        return PdfExtractor()
    elif fmt == "docx":
        return DocxExtractor()
    else:
        # Should not be reached due to validate_filepath/detect_file_format
        raise ValueError(f"No extractor available for format: {fmt}")
