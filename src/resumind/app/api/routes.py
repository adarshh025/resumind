from fastapi import APIRouter, UploadFile, File, Depends
from resumind.app.api.models import ParseResponse, HealthResponse
from resumind.app.services.upload import UploadService

router = APIRouter()
upload_service = UploadService()

@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse()

@router.post("/resumes/parse", response_model=ParseResponse)
async def parse_resume(file: UploadFile = File(...)):
    """
    Accepts a resume file (PDF, DOCX) via multipart upload, parses it, and returns a unified structured representation.
    """
    return await upload_service.process_upload(file)
