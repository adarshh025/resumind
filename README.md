# Resumind

**Intelligent Resume Analysis & Structured Extraction Engine**

## Overview
Resumind is an advanced, practical Automated Resume Analyzer designed for Job Portals and HR systems. It focuses on correctness, maintainability, determinism, and modular architecture. 

The core engine is designed as a standalone Python library capable of handling PDF and DOCX formats. It extracts text, cleans formatting artifacts, logically segments resume sections, and extracts structured information (such as Contact Info, Skills, Education, Experience, Projects) using a hybrid NLP (spaCy) and rules-based approach.

## Features
- **Document Ingestion**: Seamlessly reads `.pdf` and `.docx` files.
- **Section Segmentation**: Heuristically splits resumes into standard sections (Experience, Education, Skills, Projects, Summary).
- **Information Extraction**: Uses high-precision regex and NLP (Named Entity Recognition) to pull Contact Information, Candidate Names, Roles, Organizations, and Dates.
- **Context-Aware Skill Extraction**: Built-in ontology resolves abbreviations (e.g. `React.js` -> `React`) and uses word boundaries to prevent false positives (e.g., distinguishing the word "go" from the programming language "Go").
- **Structured Output**: Validates and serializes extracted data into a strict, predictable JSON schema using Pydantic.
- **Local & Private**: Processes resumes 100% offline. No third-party AI APIs, LLM calls, or cloud dependencies.

## Architecture & Processing Pipeline
Resumind processes documents through a deterministic, traceable pipeline:

```text
Resume File (.pdf / .docx)
    ↓
Document Extraction (pdfminer.six / python-docx)
    ↓
Text Cleaning (Normalization, bullet canonicalization)
    ↓
Section Detection (Heuristic boundary inference)
    ↓
Contact & Metadata Extraction (Regex)
    ↓
NER Semantic Extraction (spaCy en_core_web_sm)
    ↓
Skill Ontology Binding (Canonical mapping)
    ↓
Resume Assembly (Cross-referencing entities into Pydantic models)
    ↓
API Response / Web UI
```

## Requirements
- **Python**: 3.11+
- **Core Dependencies**: `spacy`, `pdfminer.six`, `python-docx`, `pydantic`, `fastapi`

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/adarshh025/resumind.git
cd resumind
```

### 2. Set Up a Virtual Environment (Windows)
```cmd
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install the Project
Install the core requirements and development tools:
```cmd
pip install -e .[dev]
```

### 4. Download the Local NLP Model
Resumind requires the lightweight English spaCy model to perform Named Entity Recognition (NER) locally:
```cmd
python -m spacy download en_core_web_sm
```

## Running Resumind (Web Interface & API)

Resumind includes a FastAPI backend and a clean, functional web interface to test the parser.

1. Activate your virtual environment:
   ```cmd
   .\.venv\Scripts\activate
   ```
2. Start the FastAPI server:
   ```cmd
   uvicorn src.resumind.app.main:app --reload
   ```
3. Open your browser and navigate to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

From the UI, you can upload `.pdf` or `.docx` files and instantly see the structured extraction results. You can also view and copy the raw JSON payload.

## API Usage

You can process resumes programmatically via the REST API. 
The endpoint accepts a standard `multipart/form-data` file upload.

### Example Request (cURL)
```cmd
curl -X POST -F "file=@sample_resume.pdf" http://127.0.0.1:8000/api/v1/resumes/parse
```

### Example Response (Truncated JSON)
```json
{
  "status": "success",
  "resume": {
    "metadata": {
      "file_name": "sample_resume.pdf",
      "file_type": "pdf",
      "processing_timestamp": "2026-09-14T10:00:00Z"
    },
    "candidate": {
      "name": "Jane Doe",
      "location": "San Francisco"
    },
    "contact": {
      "emails": ["jane.doe@example.com"],
      "phones": ["+1-555-0123"],
      "linkedin": ["linkedin.com/in/janedoe"],
      "github": ["github.com/janedoe"],
      "portfolios": [],
      "other_urls": []
    },
    "skills": [
      {
        "canonical_name": "Python",
        "category": "Language",
        "mentions": []
      }
    ],
    "experience": [],
    "education": [],
    "projects": [],
    "summary": "Experienced software engineer..."
  },
  "warnings": []
}
```

## Testing
Tests are written using `pytest`. The suite includes unit tests, ingestion integration tests, and adversarial NLP edge-case testing.
```bash
pytest tests/
```

## Security & Privacy
- **100% Local**: No resume content is ever sent to external cloud APIs or LLM providers.
- **Secure File Handling**: Uploaded files are streamed directly into secure OS-level temporary files, processed, and explicitly unlinked in a `finally` block. No user data remains on disk.
- **Size Limits**: The API strictly enforces a 5MB maximum file size to prevent memory exhaustion (HTTP 413).

## Limitations
- **No OCR**: Resumind extracts embedded text only. Image-only (scanned) PDFs will gracefully yield empty results rather than hallucinating data.
- **Complex Layouts**: Highly complex multi-column PDFs rely on `pdfminer.six` reading-order heuristics. Severe layout fragmentation can occasionally cause sentence splicing.
- **Language**: The parser and `en_core_web_sm` model are optimized exclusively for English resumes.
- **Synchronous NLP**: The core `parsefile()` logic is currently synchronous. For high-throughput concurrent API usage, this logic should be offloaded to a background task queue (e.g. Celery).

## Project Structure
```text
resumind/
├── docs/                # Architecture, requirements, and testing docs
├── src/
│   └── resumind/
│       ├── app/         # FastAPI web server and frontend static files
│       ├── assembly/    # Pydantic data modeling and unification
│       ├── ingestion/   # PDF and DOCX readers
│       ├── nlp/         # SpaCy NER and Skill ontologies
│       ├── preprocessing/# Noise removal and text cleaning
│       ├── segmentation/# Section boundary detection
│       └── parser.py    # Main orchestrator pipeline
├── tests/               # Pytest suite including adversarial tests
├── pyproject.toml       # Python package configuration
├── README.md            # You are here
├── LICENSE              # MIT License
└── .gitignore
```

## Future Scope
- Adding explicit OCR fallback (e.g. Tesseract) for scanned PDFs.
- Implementing an asynchronous Celery worker for heavy concurrent API traffic.
- Expanding the Skill Ontology with dynamically loaded JSON mappings.
- Training a custom SpaCy NER model specifically on Resume layouts.

## License
MIT License. Copyright (c) 2026 Adarsh Aher.

## Author
Adarsh Aher (aheradarsh6@gmail.com)
