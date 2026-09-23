# Resumind: Project Contract

This document defines the permanent engineering contract and architectural principles of Resumind.

## 1. Project Identity
- **Project Name**: Resumind
- **Description**: Automated Resume Analyzer for Job Portals
- **Author**: Adarsh Aher (Email: aheradarsh6@gmail.com, GitHub: https://github.com/adarshh025)
- **Repository**: https://github.com/adarshh025/resumind
- **License**: MIT License (Copyright © 2026 Adarsh Aher)

## 2. Requirements & Constraints
- The project is implemented against the Persevex specification: *"Automated Resume Analyzer for Job Portals"*.
- **Mandatory Deliverables**:
  1. Core parsing library with `ResumeParser.parsefile(filepath)`.
  2. Standalone evaluator CLI (`python parser.py <filepath>`).
  3. Skill knowledge base (`skills.json`) with canonical names, categories, and aliases.
  4. FastAPI REST wrapper (`POST /api/v1/resumes/parse`) and web interface.
  5. 10–20 resume layout test suite with semantic validation.
- **Architectural Rules**:
  - Deterministic and local execution: Zero external network calls, zero cloud dependencies, zero paid APIs.
  - Reproducibility: Clean installation on standard Python 3.11 environments.
  - Privacy and Security: Zero retention of uploaded resumes; immediate temporary file cleanup; no secrets or personal resumes in repository.
  - Technical Integrity: No fabricated performance claims, fake benchmarks, or unverified claims.

## 3. Technology Baseline
- **Language**: Python 3.11
- **Packaging**: Standard PEP 621 `pyproject.toml` (using `hatchling` build backend).
- **Core Dependencies**:
  - `spacy>=3.7.0` (Pretrained English NER `en_core_web_sm`)
  - `pdfminer.six>=20231228` (PDF text and layout extraction)
  - `python-docx>=1.1.0` (DOCX paragraph and table parsing)
  - `pydantic>=2.7.0` (Data validation and JSON serialization)
  - `fastapi>=0.110.0` (REST API)
  - `uvicorn>=0.29.0` (ASGI server)
  - `python-multipart>=0.0.9` (Multipart upload handling)
- **Testing**: `pytest>=8.0.0`

## 4. Pipeline Architecture
```
Input File (.pdf / .docx)
    │
    ▼
Ingestion Layer (PdfExtractor / DocxExtractor)
    │
    ▼
Preprocessing Layer (ResumeCleaner: NFKC, whitespace, divider filtration)
    │
    ▼
Segmentation Layer (Sectionizer: exact & inline heading detection, scoring)
    │
    ▼
Information Extraction Layer
    ├── ContactExtractor (Emails, Phones, URLs)
    ├── SemanticEntityExtractor (Candidate, Org, Date, Location)
    └── SkillExtractor (75 canonical skills, aliases, ambiguity guards)
    │
    ▼
Assembly Layer (ResumeAssembler: role/org split, degree/inst split, Pydantic model)
    │
    ▼
Structured JSON Output
```

## 5. Maintenance Guidelines
Every contribution or modification MUST:
1. Maintain 100% test pass rate on `pytest tests/`.
2. Preserve existing public APIs (`ResumeParser.parsefile()`, `/api/v1/resumes/parse`).
3. Maintain zero-cloud, privacy-preserving local execution.
