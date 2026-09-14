# Resumind Architecture

## Core Philosophy
Resumind is structured as a modular data pipeline. The core engine is decoupled from any API or UI layer, allowing it to function as a standalone Python library.

## Module Boundaries
- `resumind.ingestion`: Centralized document ingestion layer. Uses a Factory pattern (`get_extractor`) returning a `DocumentExtractor` interface (`PdfExtractor` or `DocxExtractor`). Validates paths, gracefully handles missing/corrupt documents, parses tables/runs in DOCX files, and tracks empty/scanned PDFs to output a normalized `DocumentExtractionResult` model.
- `resumind.preprocessing`: Centralized text cleaning pipeline (`ResumeCleaner`). Applies Unicode (NFKC) normalization, handles control characters, canonicalizes bullet points (`-`), strips page markers, and collapses repetitive whitespace while strictly preserving line boundaries. Non-destructive.
- `resumind.segmentation`: Heuristically divides the cleaned text into logical sections using the `Sectionizer`. Evaluates lines with a confidence score to detect section headings, handles duplicate sections, and maps to canonical section definitions (`contact_header`, `experience`, `education`, `skills`, `summary`, `projects`, `unknown`). Output is a list of `SectionBlock`s.
- `resumind.extraction`: Orchestrates specific extraction layers over the segmented text. Currently includes `ContactExtractor` which uses high-precision Regex, formatting heuristics, and domain rules to extract and deduplicate emails, phone numbers, and various URL classes (LinkedIn, GitHub, Portfolios) while strongly rejecting false positives like GPAs or dates. Output populates the `ContactInfo` model.
- `resumind.nlp`: The Semantic Entity Layer. `SemanticEntityExtractor` drives a hybrid NLP engine (powered by `spaCy` `en_core_web_sm`) to interpret the semantics of resume text. It extracts `CANDIDATE`, `ORGANIZATION`, `DATE`, `LOCATION` while retaining contextual source tracking.
- `resumind.extraction`: A dedicated module for advanced extraction heuristics. It contains `SkillExtractor` which utilizes a centralized JSON ontology (`data/skills.json`) to perform contextual skill matching.
- `resumind.assembly`: The Unified Orchestration Layer. `ResumeAssembler` converts the disjointed extractions into a traceable schema. It groups entities into cohesive `Experience`, `Education`, and `Project` blocks using advanced heuristic logic.
- `resumind.models`: The canonical data models using Pydantic for validation and serialization. Contains `ResumeData`, the final API-ready JSON output structure.
- `resumind.app`: The Presentation Layer. A FastAPI application (`main.py`) exposing REST endpoints (`/api/v1/resumes/parse`) and serving a lightweight vanilla HTML/JS/CSS web interface. Safely manages temporary file uploads, HTTP error serialization, and cleanly passes execution down to the core parser domain.
- `resumind.validation`: Post-extraction validation and confidence scoring.

## Future Layers
- **API**: A `FastAPI` application that wraps `ResumeParser`.
- **UI**: A lightweight, responsive frontend for demonstration purposes.
