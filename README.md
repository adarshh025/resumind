# Resumind

A Python-based resume parsing and structured information extraction library.

Resumind ingests PDF and DOCX documents, cleans text artifacts, heuristically segments resume sections, and extracts entities (contact information, candidate name, organizations, dates, and skills) into a validated JSON schema.

## Features

- **Format Support**: Processes `.pdf` and `.docx` files.
- **Section Detection**: Segments text into predefined blocks (Experience, Education, Skills, Projects, Summary).
- **Entity Extraction**: Uses regex for contact metadata and spaCy for Named Entity Recognition (NER).
- **Skill Canonicalization**: Maps raw string matches to a predefined skill ontology.
- **Validation**: Strict JSON serialization using Pydantic.
- **Local Execution**: Runs entirely offline with no external API dependencies.

## Architecture

1. **Ingestion**: `pdfminer.six` / `python-docx`
2. **Preprocessing**: Unicode normalization and control character stripping
3. **Segmentation**: Rule-based boundary detection
4. **Extraction**: Hybrid regex and `en_core_web_sm` (spaCy) pipeline
5. **Assembly**: Pydantic model cross-referencing and validation
6. **Interface**: FastAPI REST endpoints and static HTML/JS frontend

## Requirements

- Python 3.11+

## Installation

```bash
git clone https://github.com/adarshh025/resumind.git
cd resumind

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows

# Install package and dependencies
pip install -e .[dev]

# Download required spaCy language model
python -m spacy download en_core_web_sm
```

## Usage

### Starting the Server

```bash
uvicorn src.resumind.app.main:app --reload
```
The web interface is available at `http://127.0.0.1:8000`.

### REST API

**Endpoint**: `POST /api/v1/resumes/parse`
**Content-Type**: `multipart/form-data`

```bash
curl -X POST -F "file=@sample.pdf" http://127.0.0.1:8000/api/v1/resumes/parse
```

**Response Schema**
```json
{
  "status": "success",
  "resume": {
    "metadata": {
      "file_name": "sample.pdf",
      "file_type": "pdf",
      "processing_timestamp": "2026-09-14T10:00:00Z"
    },
    "candidate": {
      "name": "Jane Doe",
      "location": "San Francisco"
    },
    "contact": {
      "emails": ["jane.doe@example.com"],
      "phones": ["+1-555-0123"]
    },
    "skills": [],
    "experience": [],
    "education": [],
    "projects": []
  },
  "warnings": []
}
```

## Testing

Run the test suite via pytest:
```bash
pytest tests/
```

## Limitations

- **OCR**: Does not support image-based PDFs. Requires extractable text streams.
- **Layouts**: Highly complex multi-column PDFs may result in fragmented reading orders due to `pdfminer.six` heuristics.
- **Language**: Models and rules are optimized exclusively for English.
- **Concurrency**: The extraction pipeline is CPU-bound and synchronous.

## License

MIT License. Copyright (c) 2026 Adarsh Aher.
