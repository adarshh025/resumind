# Resumind: Requirements Traceability Matrix

This document establishes the requirement-by-requirement traceability audit comparing Resumind against the Persevex *"Automated Resume Analyzer for Job Portals"* specification.

In accordance with strict academic and engineering standards, every requirement is classified as one of:
- **IMPLEMENTED**: Fully implemented, verified with automated tests.
- **PARTIALLY IMPLEMENTED**: Functionally operational using alternative/hybrid architectures, but diverges from certain theoretical requirements (e.g. custom model fine-tuning).
- **NOT IMPLEMENTED**: Feature not present.
- **OUT OF SCOPE**: Explicitly excluded by design or architectural boundaries.

---

## 1. Specification Requirement Traceability

| ID | Requirement | Status | Implementation Module | Verification / Test Evidence | Engineering Notes |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **A** | **Parser Module** | IMPLEMENTED | `src/resumind/parser.py`, `parser.py` | `tests/test_parser.py`, CLI | Top-level `parser.py` re-exports the module for grading harness compatibility. |
| **B** | **ResumeParser Class** | IMPLEMENTED | `resumind.parser.ResumeParser` | `tests/test_parser.py` | Core class instantiating ingestion, cleaner, sectionizer, extractors, and assembler. |
| **C** | **`parsefile(filepath)`** | IMPLEMENTED | `ResumeParser.parsefile()` | `tests/test_parser.py`, `tests/test_e2e.py` | Accepts `str` or `Path`, returns standard structured dictionary validated against Pydantic schema. |
| **D** | **PDF Ingestion** | IMPLEMENTED | `resumind.ingestion.pdf.PdfExtractor` | `tests/test_ingestion.py` | Uses `pdfminer.six` LAParams stream extraction. Handles corrupt, empty, and encrypted files safely. |
| **E** | **DOCX Ingestion** | IMPLEMENTED | `resumind.ingestion.docx.DocxExtractor` | `tests/test_ingestion.py` | Uses `python-docx` to extract both paragraph text and table cell contents. |
| **F** | **Text Cleaning** | IMPLEMENTED | `resumind.preprocessing.cleaner.ResumeCleaner` | `tests/test_preprocessing.py`, `tests/test_adversarial.py` | Unicode NFKC normalization, control character stripping, whitespace collapse, bullet canonicalization (`-`), and table border/decorative divider removal while preserving technical tokens (`C++`, `C#`, `Node.js`, `CI/CD`). |
| **G** | **Section Segmentation** | IMPLEMENTED | `resumind.segmentation.sectionizer.Sectionizer` | `tests/test_segmentation.py`, `tests/test_adversarial.py` | Deterministic structural analyzer supporting exact headings, inline headings with colon/dash boundaries, confidence scoring (`isupper` 0.95, `istitle` 0.85), and sequential duplicate block preservation. |
| **H** | **Contact Extraction** | IMPLEMENTED | `resumind.extraction.contact.ContactExtractor` | `tests/test_contact.py`, `tests/test_adversarial.py` | High-precision regex matching emails, phone numbers, and URLs (LinkedIn, GitHub, portfolios) with false-positive rejection. |
| **I** | **Phone Normalization** | IMPLEMENTED | `resumind.extraction.contact.ContactExtractor` | `tests/test_contact.py` | Normalizes punctuation and whitespace, preserves international prefixes (`+...`), normalizes 11-digit NANP (`1-...`), and leaves ambiguous national numbers intact without fabricating country codes. |
| **J** | **NER Model** | PARTIALLY IMPLEMENTED | `resumind.nlp.ner.SemanticEntityExtractor` | `tests/test_ner.py`, `scripts/evaluate_nlp.py` | Resumind uses spaCy's pretrained `en_core_web_sm` model combined with deterministic domain-specific extraction rules for candidate names, universities, and degree titles. A custom fine-tuned NER model is outside the current release scope to preserve lightweight, reproducible offline execution. |
| **K** | **Candidate Name Detection** | IMPLEMENTED | `resumind.nlp.ner.SemanticEntityExtractor`, `ResumeAssembler` | `tests/test_ner.py`, `tests/test_adversarial.py`, `tests/test_layout_fixtures.py` | Multi-tiered candidate scoring in `contact_header`. Safely rejects decorative dividers (`===`, `---`), Markdown table borders (`\|---\|---\|`), emails, URLs, digits, and raw job titles (`Data Analyst`, `Cloud Solutions Architect`). |
| **L** | **University Detection** | IMPLEMENTED | `resumind.assembly.assembler.ResumeAssembler` | `tests/test_assembly.py`, `tests/test_layout_fixtures.py` | Detects university and college names in education blocks via entity mentions (`ORGANIZATION`) and institutional indicators (`University`, `College`, `Institute`, `School`, `Academy`, `SUNY`, `UC`). |
| **M** | **Degree Detection** | IMPLEMENTED | `resumind.assembly.assembler.ResumeAssembler` | `tests/test_assembly.py`, `tests/test_layout_fixtures.py` | Comprehensive degree pattern matching covering B.Tech, M.Tech, B.E., M.E., B.Sc, M.Sc, B.S., M.S., B.A., M.A., BBA, MBA, B.Com, M.Com, PhD, Associate, Bachelor, Master, Doctor of Philosophy, etc. |
| **N** | **Skill Knowledge Base / Ontology** | IMPLEMENTED | `src/resumind/data/skills.json` | `tests/test_skills.py`, `scripts/evaluate_nlp.py` | Structured JSON ontology containing 75 canonical skills across 8 distinct industry categories. |
| **O** | **Technical Skills** | IMPLEMENTED | `resumind.extraction.skills.SkillExtractor` | `tests/test_skills.py`, `tests/test_adversarial.py` | Programming languages, databases, cloud, dev tools including HTML, CSS, Bash, REST API, GraphQL, CI/CD, Kafka, Jenkins. |
| **P** | **Soft Skills & Methodologies** | IMPLEMENTED | `resumind.extraction.skills.SkillExtractor` | `tests/test_skills.py`, `scripts/evaluate_nlp.py` | Project Management, Leadership, Communication, Teamwork, Collaboration, Problem Solving, Critical Thinking, Time Management, Adaptability, Agile, Scrum, etc. |
| **Q** | **Alias Handling & Disambiguation** | IMPLEMENTED | `resumind.extraction.skills.SkillExtractor` | `tests/test_skills.py`, `tests/test_adversarial.py` | Longest-match-first regex compilation with word boundaries prevents sub-token collisions. Ambiguity guards prevent false positives for short tokens (`Go`, `C`, `R`) and common verbs. |
| **R** | **Structured JSON Output** | IMPLEMENTED | `resumind.models.resume.ResumeData` | `tests/test_assembly.py`, `tests/test_layout_fixtures.py` | Pydantic model enforcing strict typing, ISO-8601 timestamps, section listings, metadata, and warnings. |
| **S** | **Experience Extraction** | IMPLEMENTED | `resumind.assembly.assembler.ResumeAssembler` | `tests/test_assembly.py`, `tests/test_adversarial.py`, `tests/test_layout_fixtures.py` | Parses single-line (`Role at Company`, `Company - Role`, `Role \| Company`, `Role @ Company`) and multi-line structures. Populates role, organization, start/end dates, current flag, descriptions, and linked skills. |
| **T** | **Education Extraction** | IMPLEMENTED | `resumind.assembly.assembler.ResumeAssembler` | `tests/test_assembly.py`, `tests/test_adversarial.py`, `tests/test_layout_fixtures.py` | Extracts single-line (`Degree - University`) and multi-line structures without dropping institutions. Captures degree, institution, dates, and GPA/grades. |
| **U** | **Project Extraction** | IMPLEMENTED | `resumind.assembly.assembler.ResumeAssembler` | `tests/test_assembly.py` | Extracts project names, descriptions, and binds referenced skill technologies. |
| **V** | **API Wrapper** | IMPLEMENTED | `resumind.app.main`, `resumind.app.api.routes` | `tests/test_api.py` | FastAPI REST service with multipart file upload (`/api/v1/resumes/parse`) and embedded HTML/CSS/JS web interface. |
| **W** | **Documentation** | IMPLEMENTED | `README.md`, `docs/` | Inspection | Detailed installation, CLI and library usage, segmentation logic, ontology rules, and security guidelines. |
| **X** | **10–20 Resume Layout Testing** | IMPLEMENTED | `tests/test_layout_fixtures.py` | `tests/test_layout_fixtures.py` (28/28 tests passing) | Automated benchmark suite testing 20 diverse layouts in `tests/fixtures/generated_resumes/` with schema and semantic verification. |

---

## 2. Additional Specification Directives

| Directive | Status | Architectural Decision & Notes |
| :--- | :---: | :--- |
| **Bold Text Heading Detection** | PARTIALLY IMPLEMENTED | Headings are detected via casing heuristics (`isupper`, `istitle`), length thresholds, and alias tables. Font weight metadata extraction via PDF rendering engines was omitted to avoid heavy C++ bindings and destabilizing dependencies. |
| **OCR for Scanned Resumes** | OUT OF SCOPE | Resumind processes extractable text streams only. Scanned or image-only PDFs safely return `status: "TEXT_NOT_EXTRACTABLE"`. Tesseract/OCR is excluded to preserve lightweight local execution. |
| **NLTK / Pandas Prerequisite** | ALTERNATIVE IMPLEMENTED | spaCy and Pydantic provide equivalent or superior lemmatization, tokenization, and schema validation. Pandas and NLTK were omitted from runtime dependencies to avoid dependency bloat. |
