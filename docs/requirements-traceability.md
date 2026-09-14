# Resumind Requirements Traceability Matrix

This document maps the core architectural and functional requirements from the initial project specification to their actual implementation and verification status.

## 1. Project Infrastructure
| Requirement | Status | Implementation | Test Coverage | Notes |
|-------------|--------|----------------|---------------|-------|
| Modular Pipeline | VERIFIED | `src/resumind/` architecture separates concerns (ingestion, nlp, app). | Verified structurally. | The `ResumeParser` class acts as the clean orchestration layer. |
| Strict Schema Contract | VERIFIED | `src/resumind/models/resume.py` uses `pydantic`. | `tests/test_api.py` | Enforces strong typing. |

## 2. Ingestion Layer
| Requirement | Status | Implementation | Test Coverage | Notes |
|-------------|--------|----------------|---------------|-------|
| Extract PDF Text | VERIFIED | `pdfminer.six` in `ingestion/pdf.py` | `tests/test_ingestion.py` | Extracts textual PDFs. |
| Extract DOCX Text | VERIFIED | `python-docx` in `ingestion/docx.py` | `tests/test_ingestion.py` | Support for paragraphs/tables. |
| Scanned PDF Handling | WEAKLY VERIFIED | `ingestion/pdf.py` returns `TEXT_NOT_EXTRACTABLE` | Included in E2E tests, needs explicit adversarial test. | OCR is explicitly NOT implemented (documented limitation). |

## 3. Cleaning & Segmentation
| Requirement | Status | Implementation | Test Coverage | Notes |
|-------------|--------|----------------|---------------|-------|
| Unprintable Char Removal | VERIFIED | `cleaner.py` using regex `[^\x00-\x7F]+` | `tests/test_preprocessing.py` | |
| Robust Section Detection | VERIFIED | `sectionizer.py` matches known headings. | `tests/test_segmentation.py` | Maps custom headers to "Unknown" rather than deleting. |

## 4. Contact Extraction
| Requirement | Status | Implementation | Test Coverage | Notes |
|-------------|--------|----------------|---------------|-------|
| Email & Phone | VERIFIED | Regex patterns in `contact.py` | `tests/test_contact.py` | |
| GitHub & LinkedIn | VERIFIED | Normalization and extraction regex. | `tests/test_contact.py` | |
| Avoid numeric collisions | WEAKLY VERIFIED | Phone regex requires min digits. | Needs adversarial test (e.g. 2021-2025). |

## 5. NLP & NER
| Requirement | Status | Implementation | Test Coverage | Notes |
|-------------|--------|----------------|---------------|-------|
| SpaCy Integration | VERIFIED | `ner.py` uses `en_core_web_sm`. | `tests/test_ner.py` | Offline model. |
| Candidate Name Fallback | WEAKLY VERIFIED | Top section fallback in `assembler.py`. | Needs adversarial test against "RESUME" headings. |

## 6. Skill Extraction
| Requirement | Status | Implementation | Test Coverage | Notes |
|-------------|--------|----------------|---------------|-------|
| Alias Resolution | VERIFIED | `ontology.json` compiled to regex. | `tests/test_skills.py` | Maps `sklearn` to `scikit-learn`. |
| Explicit-Only Rule | VERIFIED | System only extracts matching text. | Verified architecturally (No LLM). | No inferred skills are hallucinated. |
| Avoid Generic Collisions | WEAKLY VERIFIED | Word boundaries `\b` applied. | Needs adversarial testing for words like "Go" or "R". |

## 7. Assembly & Schema
| Requirement | Status | Implementation | Test Coverage | Notes |
|-------------|--------|----------------|---------------|-------|
| Experience Clustering | WEAKLY VERIFIED | `ResumeAssembler` clusters dates/orgs. | `tests/test_assembly.py` | Needs adversarial out-of-order test. |
| Evidence Tracing | VERIFIED | Output retains source text spans. | `tests/test_assembly.py` | |

## 8. Web API & Security
| Requirement | Status | Implementation | Test Coverage | Notes |
|-------------|--------|----------------|---------------|-------|
| No Fake Analytics | VERIFIED | UI renders JSON 1:1 in `app.js`. | Manual Audit | No arbitrary scores/match ratings. |
| Privacy Cleanups | VERIFIED | `finally: os.unlink()` in `upload.py`. | Tested locally. | Temporary files are not preserved. |
| 5MB Upload Limit | VERIFIED | Checked on stream in `upload.py`. | `tests/test_api.py` | Protects from OOM. |
| XSS Escaping | VERIFIED | `escapeHTML` in `app.js`. | Manual Audit | |
| Offline First | VERIFIED | No external network calls exist. | Source code review. | |
