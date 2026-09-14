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

## 7. Current Phase Status
- **Phase 1 (Complete)**: Foundation and Architecture
- **Phase 2 (Complete)**: Production-Grade Document Ingestion & Text Extraction Engine. Extractor interfaces (`DocumentExtractor`), robust error handling (avoiding raw stack traces), and privacy-safe logging have been established.
- **Phase 3 (Complete)**: Text Cleaning & Section Segmentation. Implemented non-destructive text cleaning (`cleaned_text`) and a deterministic hybrid heading detector that safely bins lines into `SectionBlock` elements without destroying information or using NLP models prematurely.
- **Phase 4 (Complete)**: High-Precision Contact & Metadata Extraction. Implemented robust regex-based extraction for emails, phone numbers, and URLs. The system handles false-positive elimination (e.g., rejecting dates as phones), normalizes outputs, deduplicates lists, and bins URLs into specific sub-categories (LinkedIn, GitHub, Portfolio).
- **Phase 5 (Complete)**: NLP Named Entity Recognition & Semantic Entity Layer. Integrated a hybrid NER engine (`spaCy` + section heuristics) to extract `CANDIDATE`, `ORGANIZATION`, `DATE`, and `LOCATION` entities with gracefully fallback to regex rules if the NLP model isn't completely confident.
- **Phase 6 (Complete)**: Skill Ontology & Context-Aware Extraction. Built a maintainable JSON skill ontology that supports canonical forms, extensive aliases, and semantic categories. The `SkillExtractor` strictly evaluates word boundaries and contexts. Captures specific skill versions and deduplicates identical string matches. Supports only explicit extraction currently to maintain precision over loose inference.
- **Phase 7 (Complete)**: Unified Schema & Structured Resume Assembly. Built `ResumeAssembler` to integrate outputs from all previous modules without duplicating logic. Created the final `ResumeData` Pydantic schema enforcing typing, optional fields, and evidence traceability. Developed advanced clustering heuristics for Experience and Education blocks to handle multiple NER dates and organizations, explicitly separating candidate data from generic contacts, and generating a 100% backend-independent JSON output.
- **Phase 8 (Complete)**: FastAPI Backend & Web UI. Built `resumind.app` wrapping the core parser in a robust REST API (`/api/v1/resumes/parse`) using `FastAPI` and `python-multipart`. Enforces a strict 5MB upload limit, validates allowed formats (`.pdf`, `.docx`), guarantees temporary file cleanup regardless of parser outcome, and standardizes errors. Features a vanilla HTML/JS/CSS frontend built for engineering clarity without bloated JS frameworks or fake UI analytics. Supports JSON inspection and copying.
- **Phase 9 (Complete)**: Testing, Benchmarking, and Hardening. Executed a massive audit across the entire codebase. Verified a 100% passing test suite with zero failures (48/48 tests). Conducted a full simulated clean installation to ensure cross-platform Python reproducibility. Completed extensive security testing (XSS escapes, path traversal blocks, oversized upload drops, strict temporary cleanup hooks) and created comprehensive evaluation reporting (`docs/evaluation.md`) mapping performance baselines.

## 8. Execution Rules for Future Phases
Every future development phase MUST:
1. Read this `PROJECT_CONTRACT.md`.
2. Inspect the current repository.
3. Preserve working functionality.
4. Modify architecture only when technically justified.
5. Never silently contradict previous phases.
