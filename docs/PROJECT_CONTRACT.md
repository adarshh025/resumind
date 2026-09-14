# Resumind Project Contract

This document is the permanent architectural contract of Resumind. All future phases MUST follow these principles.

## 1. Project Identity
- **Project Name**: Resumind
- **Description**: Intelligent Resume Analysis & Structured Extraction Engine
- **Developer**: Adarsh Aher (aheradarsh6@gmail.com, GitHub: https://github.com/adarshh025)
- **License**: MIT License (Copyright © 2026 Adarsh Aher)

## 2. Requirements & Constraints
- The project is based on the Persevex specification: "Automated Resume Analyzer for Job Portals".
- **Mandatory Requirements**: PDF/DOCX ingestion, text cleaning, section segmentation, contact extraction, NER, skill extraction/normalization with a knowledge base, and structured nested JSON output.
- **Non-Negotiable**: No fake AI features, no paid APIs, no required internet connectivity for the core engine. Prioritize correctness, maintainability, and clean code.

## 3. Technology Decisions
- **Language**: Python 3.11 (chosen for stability and precompiled wheel support for NLP/ML dependencies).
- **Packaging**: PEP 621 compliant `pyproject.toml` (using `hatchling`).
- **Core Dependencies**: `pdfminer.six` (PDF), `python-docx` (DOCX), `spacy` (NLP), `pydantic` (Data Validation/Serialization).
- **Testing**: `pytest`.

## 4. Architecture
The core system MUST remain usable as an independent Python library.
**Conceptual Pipeline**:
Resume File -> Document Ingestion -> Raw Text -> Text Cleaning -> Section Segmentation -> Information Extraction -> Normalization -> Validation -> Structured Resume Object -> JSON Output

## 5. Core Interfaces
- **`src/resumind/parser.py`**: Must contain `class ResumeParser` with a `parsefile(filepath)` method.
- **Canonical Data Model**: Defined using `pydantic` in `src/resumind/models/resume.py`.

## 6. Security, Privacy & Testing
- Do not transmit resume content externally.
- Do not commit private/sample personal resumes.
- System must be tested against 10–20 materially different real-world layouts.

## 7. Implemented Capabilities
- **Foundation and Architecture**: Modular pipeline orchestration.
- **Document Ingestion & Text Extraction Engine**: Extractor interfaces (`DocumentExtractor`), robust error handling, and privacy-safe logging.
- **Text Cleaning & Section Segmentation**: Non-destructive text cleaning (`cleaned_text`) and a deterministic hybrid heading detector.
- **High-Precision Contact & Metadata Extraction**: Robust regex-based extraction for emails, phone numbers, and URLs with false-positive elimination.
- **NLP Named Entity Recognition & Semantic Entity Layer**: Hybrid NER engine (`spaCy` + section heuristics) to extract `CANDIDATE`, `ORGANIZATION`, `DATE`, and `LOCATION` entities.
- **Skill Ontology & Context-Aware Extraction**: JSON skill ontology supporting canonical forms and aliases.
- **Unified Schema & Structured Resume Assembly**: `ResumeAssembler` integrates outputs into a single `ResumeData` Pydantic schema enforcing typing.
- **FastAPI Backend & Web UI**: REST API (`/api/v1/resumes/parse`) using `FastAPI` enforcing a strict 5MB upload limit. Features a vanilla HTML/JS/CSS frontend.
- **Testing, Benchmarking, and Hardening**: 100% passing test suite with zero failures. Extensive security testing (XSS escapes, path traversal blocks, oversized upload drops, strict temporary cleanup hooks).

## 8. Execution Rules for Future Development
Every future pull request or feature addition MUST:
1. Adhere to this `PROJECT_CONTRACT.md`.
2. Preserve existing functionality and pass all tests.
3. Modify core architecture only when technically justified.
