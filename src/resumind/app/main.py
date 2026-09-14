from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pathlib import Path

from resumind.app.api.routes import router as api_router
from resumind.app.api.models import APIErrorResponse

app = FastAPI(
    title="Resumind API",
    description="Intelligent Resume Analysis & Structured Extraction Engine",
    version="1.0.0"
)

# Custom exception handlers for consistent API error responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        return JSONResponse(status_code=exc.status_code, content={"error": detail})
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": "INTERNAL_ERROR", "message": str(detail)}})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "INVALID_REQUEST", "message": "Validation failed for request"}}
    )

# Include API Router
app.include_router(api_router, prefix="/api/v1")

# Mount Static Files for UI
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir.mkdir(parents=True, exist_ok=True)

app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("resumind.app.main:app", host="127.0.0.1", port=8000, reload=True)
