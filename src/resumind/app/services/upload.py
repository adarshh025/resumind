import os
import shutil
import tempfile
from pathlib import Path
from fastapi import UploadFile, HTTPException
from resumind.parser import ResumeParser
from resumind.app.api.models import ParseResponse

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

class UploadService:
    def __init__(self):
        self.parser = ResumeParser()
        
    async def process_upload(self, file: UploadFile) -> ParseResponse:
        # Validate filename
        if not file.filename:
            raise HTTPException(status_code=400, detail={"code": "INVALID_REQUEST", "message": "No filename provided"})
            
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=415, detail={"code": "UNSUPPORTED_FILE_TYPE", "message": f"Unsupported file type: {ext}"})
            
        # Create temp file safely
        fd, temp_path = tempfile.mkstemp(suffix=ext, prefix="resumind_")
        
        try:
            # Check size and write
            size = 0
            with os.fdopen(fd, 'wb') as f:
                while chunk := await file.read(8192):
                    size += len(chunk)
                    if size > MAX_FILE_SIZE:
                        raise HTTPException(status_code=413, detail={"code": "FILE_TOO_LARGE", "message": "File exceeds the 5MB limit"})
                    f.write(chunk)
                    
            if size == 0:
                raise HTTPException(status_code=400, detail={"code": "EMPTY_DOCUMENT", "message": "Uploaded file is empty"})
                
            # Run parser
            try:
                resume_data = self.parser.parsefile(temp_path)
                return ParseResponse(
                    status="success",
                    resume=resume_data,
                    warnings=resume_data.get("warnings", [])
                )
            except Exception as e:
                # Log internally, return safe error
                raise HTTPException(status_code=500, detail={"code": "PROCESSING_FAILED", "message": "An error occurred while parsing the resume"})
                
        finally:
            # Cleanup
            try:
                os.unlink(temp_path)
            except OSError:
                pass
