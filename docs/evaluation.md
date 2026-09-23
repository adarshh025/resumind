# Resumind: System Evaluation Report

**Date**: 2026-09-23

## 1. Test Environment
- **OS**: Windows 11 (win32)
- **Python Version**: 3.11.9
- **NLP Stack**: `spaCy` (`en_core_web_sm` 3.8.0)

## 2. Dataset & Fixtures
All testing was executed against completely synthetic, locally generated resumes (`tests/fixtures/generated_resumes/` and `tests/test_e2e.py`) to guarantee 100% privacy compliance. Zero applicant PII or private documents are contained within the repository.

## 3. Functional Tests (pytest)
- **Total Tests Collected**: 95
- **Passed**: 95 (100% success rate)
- **Failed**: 0
- **Skipped**: 0
- **Coverage Highlights**:
  - Ingestion (PDF/DOCX) format routing, corrupt/empty file handling, and non-extractable stream detection.
  - Cleaning & Segmentation heuristics, including Markdown table and decorative divider stripping, exact headings, and inline heading split.
  - Contact extraction, phone validation, phone normalization, and URL classification.
  - Entity extraction (spaCy NER) with candidate scoring, job title rejection, and location identification.
  - Context-aware skill extraction across 75 canonical skills with alias resolution and ambiguity guards.
  - Single-line and multi-line experience parsing (`Role at Company`, `Company - Role`, `Role | Company`).
  - Single-line and multi-line education extraction (`Degree - University`) without loss of institutional metadata.
  - End-to-end assembly into strongly typed Pydantic models.
  - FastAPI endpoints, streaming upload limits (5 MB), file validation, and exception mapping.

## 4. Layout Robustness Benchmark
- **Total Layouts Evaluated**: 20 distinct PDF layouts (`tests/fixtures/generated_resumes/`)
- **Pydantic Schema Validation**: 20/20 PASS
- **Semantic Quality Extraction**: 20/20 PASS
  - Valid candidate names verified for all 20 layouts without divider contamination.
  - Key semantic roles, organizations, degrees, and institutions verified across single-column, two-column, dense technical, and academic layouts.

## 5. NLP Evaluation (`scripts/evaluate_nlp.py`)
- **Contact Extraction**: PASS (Emails, normalized phones, and URLs extracted).
- **Technical Skill Extraction**: PASS (Resolves aliases such as `sklearn` → `scikit-learn`, `JS` → `JavaScript`, `HTML5` → `HTML`).
- **Soft Skills & Methodologies**: PASS (Detects Project Management, Agile, Scrum, Leadership, Communication, etc.).
- **Ambiguity Protection**: PASS (Tokens like "Go", "C", "R", "Bash" protected against common prose collisions).

## 6. Security & Hardening
- **XSS Prevention**: Extracted resume strings are properly escaped on the frontend (`escapeHTML()` in `app.js`).
- **Path Traversal**: Mitigated via `tempfile.mkstemp`, generating cryptographically secure OS paths and ignoring user-supplied file paths.
- **Cleanup**: `try...finally` hooks guarantee temporary `.pdf` and `.docx` files are deleted immediately after parsing.
- **Resource Exhaustion**: Strict 5 MB upload limit enforced at streaming layer, rejecting oversized payloads (`HTTP 413`).
- **Secret Scan**: Clean repository check confirmed zero API keys, tokens, credentials, or private information committed.

## 7. Overall Status
**PASS** — System meets all functional, quality, and architectural requirements for public release.
