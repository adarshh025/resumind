from abc import ABC, abstractmethod
from pathlib import Path

from resumind.ingestion.models import DocumentExtractionResult

class DocumentExtractor(ABC):
    """
    Abstract Base Class for format-specific document extractors.
    """
    
    @abstractmethod
    def extract(self, filepath: Path) -> DocumentExtractionResult:
        """
        Extracts text from the given file path.
        
        Args:
            filepath (Path): The path to the file.
            
        Returns:
            DocumentExtractionResult: The structured extraction result.
        """
        pass

def validate_filepath(filepath: Path) -> None:
    """
    Validates that a filepath exists, is a file, and has an extension.
    
    Args:
        filepath (Path): Path to validate.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If it's a directory or missing an extension.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if not filepath.is_file():
        raise ValueError(f"Path is not a valid file: {filepath}")
        
    if not filepath.suffix:
        raise ValueError(f"File has no extension: {filepath}")

def detect_file_format(filepath: Path) -> str:
    """
    Detects the canonical file format based on extension.
    
    Args:
        filepath (Path): Path to the file.
        
    Returns:
        str: "pdf" or "docx".
        
    Raises:
        ValueError: If the format is not supported.
    """
    ext = filepath.suffix.lower()
    
    if ext == ".pdf":
        return "pdf"
    elif ext == ".docx":
        return "docx"
    else:
        raise ValueError(f"Unsupported file format: '{ext}'. Only .pdf and .docx are supported.")
