# Resumind: Testing Baseline (Phase 9)

**Date**: 2026-09-14

## Environment
- **OS**: Windows (win32)
- **Python Version**: 3.11.9
- **Virtual Environment**: `.venv`

## Test Execution Summary
- **Command**: `pytest`
- **Total Tests Collected**: 48
- **Passed**: 48
- **Failed**: 0
- **Skipped**: 0
- **Warnings**: 2 (Deprecation warnings from `starlette`/`fastapi` test client internals, non-critical)
- **Duration**: ~14.85s

## Supported Formats
- **Ingestion**: PDF (`.pdf`), DOCX (`.docx`)
- **API Formats**: `multipart/form-data` uploads

## Core NLP Models
- **Library**: `spacy` v3.8.16
- **Model**: `en_core_web_sm` v3.8.0

## Core Application Dependencies
- `pydantic` v2.13.5
- `pdfminer.six` v20260107
- `python-docx` v1.2.0
- `fastapi` v0.141.1
- `uvicorn` v0.52.4
- `python-multipart` v0.0.32

## Development Dependencies
- `pytest` v9.1.1
- `fpdf2` (For synthetic test generation)
- `ruff` / `mypy` (Linters)

## Known Warnings
- Starlette Deprecation Warning: Using `httpx` with `starlette.testclient` is deprecated. (This is inside the FastAPI testing framework and does not affect production code).
- No OCR capability implemented for scanned/image-only PDFs (safely returns `TEXT_NOT_EXTRACTABLE`).

## Endpoints
- `GET /api/v1/health`
- `POST /api/v1/resumes/parse`
