import logging
from pathlib import Path
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
import pdfminer.pdfparser

from resumind.ingestion.base import DocumentExtractor
from resumind.ingestion.models import DocumentExtractionResult

logger = logging.getLogger(__name__)

class PdfExtractor(DocumentExtractor):
    def extract(self, filepath: Path) -> DocumentExtractionResult:
        result = DocumentExtractionResult(
            filename=filepath.name,
            source_format="pdf",
            raw_text="",
            status="SUCCESS"
        )
        
        try:
            pages_text = []
            page_count = 0
            
            for page_layout in extract_pages(filepath):
                page_count += 1
                page_text_blocks = []
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        text = element.get_text()
                        if text:
                            page_text_blocks.append(text)
                
                if page_text_blocks:
                    # Join text blocks with a newline to preserve some structure
                    pages_text.append("\n".join(page_text_blocks))
            
            result.page_count = page_count
            
            if not pages_text:
                result.status = "TEXT_NOT_EXTRACTABLE"
                result.warnings.append("PDF appears to be scanned or contains no extractable text.")
            else:
                # Join pages with a clear page boundary delimiter, which may be useful later
                result.raw_text = "\n\n--- PAGE_BREAK ---\n\n".join(pages_text)
                
        except pdfminer.pdfparser.PDFSyntaxError as e:
            result.status = "ERROR"
            result.errors.append(f"PDF Syntax Error: File is corrupted or malformed. {str(e)}")
            logger.error(f"Failed to extract {filepath.name}: PDF Syntax Error")
        except Exception as e:
            result.status = "ERROR"
            result.errors.append(f"Unexpected extraction error: {str(e)}")
            logger.error(f"Failed to extract {filepath.name}: Unexpected error")
            
        return result
