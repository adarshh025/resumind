# Resumind: Automated Resume Analyzer for Job Portals

An offline-first NLP engine and structured extraction pipeline for resumes in PDF and DOCX formats.

**Author**: Adarsh Aher  
**Email**: aheradarsh6@gmail.com  
**GitHub**: [https://github.com/adarshh025](https://github.com/adarshh025)  
**Repository**: [https://github.com/adarshh025/resumind](https://github.com/adarshh025/resumind)  
**License**: MIT  

---

## 1. Problem Statement

Recruitment platforms and Applicant Tracking Systems (ATS) process millions of unstructured resumes across diverse formats, visual layouts, and naming conventions. Traditional keyword searches fail to capture semantic relationships, misidentify decorative elements as candidate names, conflate job titles with personal identities, and fail when parsing single-line employment or education entries.

Resumind solves this challenge by providing a deterministic, offline-first natural language processing pipeline that ingests raw documents, removes formatting artifacts, partitions text into logical section blocks, extracts semantic entities and technical skills with alias resolution, and emits validated, strongly typed JSON representations suitable for downstream job-matching algorithms.

---

## 2. Key Features

- **Multi-Format Document Ingestion**: Native extraction for `.pdf` (via `pdfminer.six`) and `.docx` (via `python-docx`), extracting both paragraph prose and table cell contents.
- **Robust Artifact & Divider Cleaning**: Cleans Unicode characters (NFKC), normalizes bullets, and strips decorative dividers (`===`, `---`, `+-----+`) and Markdown table borders (`|---|---|`) without destroying technical tokens like `C++`, `C#`, `Node.js`, or `CI/CD`.
- **Hybrid Structural Section Segmentation**: Detects section boundaries using exact heading matches, casing heuristics (`isupper` 0.95, `istitle` 0.85), and inline heading patterns (e.g., `Experience: Principal Engineer at Google`) while preserving sequential multi-page blocks.
- **Robust Candidate Name Extraction**: Multi-tiered candidate scoring in contact headers that safely rejects email strings, URLs, phone numbers, table borders, and job titles (`Data Analyst`, `Cloud Solutions Architect`).
- **One-Line & Multi-Line Experience Parsing**: Robustly separates role and organization across common delimiters (`Role at Company`, `Company - Role`, `Role | Company`, `Role @ Company`, `Role, Company`) without losing either field.
- **Education Disambiguation**: Extracts degree titles (`B.Sc in Computer Science`, `Ph.D. in Computational Biology`) and educational institutions (`Stanford University`, `MIT`) from single-line or multi-line structures without dropping institutions.
- **Comprehensive Skill Ontology**: 75 canonical skills across 8 domains (Languages, Web, Databases, Cloud, Dev Tools, ML/AI, Management, Soft Skills) with automated alias resolution and ambiguity guards for short tokens (`Go`, `C`, `R`, `Bash`).
- **Strict Pydantic Schema Validation**: Outputs a typed, validated schema with ISO-8601 timestamps, confidence metrics, and traceability warnings.
- **Privacy-Preserving & Offline Execution**: Zero external network calls, zero third-party cloud APIs, and zero data transmission.
- **Multiple Interfaces**: Python library API, standalone CLI (`parser.py`), and FastAPI REST microservice with an interactive web UI.

---

## 3. Architecture Overview

```
Input File (.pdf / .docx)
         │
         ▼
 1. Ingestion Layer (PdfExtractor / DocxExtractor)
         │ (raw_text)
         ▼
 2. Preprocessing Layer (ResumeCleaner: NFKC, whitespace, divider filtration)
         │ (cleaned_text)
         ▼
 3. Segmentation Layer (Sectionizer: exact & inline heading detection, scoring)
         │ (SectionBlocks)
         ├─────────────────────────────────────────┐
         ▼                                         ▼
 4. ContactExtractor                       5. SkillExtractor
    (Emails, Phones, URLs)                    (75 Canonical Skills + Aliases)
         │                                         │
         ├─────────────────────────────────────────┤
         ▼                                         ▼
 6. SemanticEntityExtractor                7. ResumeAssembler
    (spaCy NER + Rule Heuristics)             (Role/Org Split, Deg/Inst Split)
         │                                         │
         └────────────────────┬────────────────────┘
                              ▼
                      8. ResumeData Model
                       (Structured JSON)
```

---

## 4. Supported File Formats

| Format | Library | Implementation Notes |
| :--- | :--- | :--- |
| **PDF (`.pdf`)** | `pdfminer.six` | Extracts flowing text streams with layout parameter tuning (`LAParams`). Gracefully detects scanned or non-extractable PDF streams. |
| **DOCX (`.docx`)** | `python-docx` | Iterates across document paragraphs and XML tables, extracting cell content and normalizing whitespace. |

---

## 5. NLP & Extraction Pipeline

### Text Cleaning & Normalization
The `ResumeCleaner` applies:
1. **Unicode Normalization**: NFKC normalization converts ligatures and irregular characters to standard UTF-8.
2. **Control Character Stripping**: Eliminates non-printable bytes while strictly preserving newline and tab boundaries.
3. **Divider & Border Removal**: Regex filters strip Markdown table syntax (`|---|---|`), decorative rules (`====================`, `--------------------`, `---------------~----`, `+------------------+`), and repetitive punctuation.
4. **Token Preservation**: Explicit lookarounds ensure tokens such as `C++`, `C#`, `.NET`, `Node.js`, `CI/CD`, and `A/B Testing` are never stripped.

### Section Segmentation Heuristics
The `Sectionizer` operates with the following rules:
- **Implicit Contact Header**: Content preceding the first detected heading is grouped into `contact_header` with confidence `1.0`.
- **Length Constraint**: Lines longer than 50 characters are rejected as headings to avoid false positives on body sentences.
- **Casing Confidence**:
  - `line.isupper()`: 0.95 confidence
  - `line.istitle()`: 0.85 confidence
  - Standard/lowercase: 0.70 confidence
- **Inline Headings**: Headings formatted as `Section: Content` (e.g., `Experience: Principal Engineer at Google`) are split; the section is registered, and the remaining content is passed into the section's line buffer.
- **Duplicate Preservation**: Multiple occurrences of the same section type across pages are preserved sequentially rather than overwritten.
- **Unknown Headings**: Unrecognized uppercase headers (`AWARDS`, `PUBLICATIONS`) are categorized as `unknown` with 0.60 confidence to ensure no candidate content is lost.

### Contact Information Extraction
The `ContactExtractor` uses targeted regular expressions:
- **Email**: Matches standard and tagged addresses (`user+tag@domain.co.in`), deduplicating across the document.
- **Phone Numbers**: Matches international and national patterns between 9 and 15 digits. Rejects false positives including dates (`2021-2025`, `12-05-2024`), version strings (`3.10.4`), 9-digit US ZIP codes (`12345-6789`), and GPA values (`3.8 / 4.0`).
- **Phone Normalization**: Preserves explicit country prefixes (`+...`), normalizes 11-digit NANP numbers (`1-xxx-xxx-xxxx`), and outputs normalized digits without fabricating arbitrary country codes.
- **URLs**: Categorizes LinkedIn profiles, GitHub accounts, and portfolio links, prefixing `https://` where protocol schemes are omitted.

### Named Entity Recognition (NER) & Candidate Detection
The `SemanticEntityExtractor` combines spaCy's pretrained `en_core_web_sm` model with domain heuristics:
- **Candidate Name Detection**: Scans the `contact_header` for candidate lines. Enforces rejection rules against job titles (`Engineer`, `Developer`, `Analyst`, `Architect`, `Consultant`, `Manager`, `Director`, `Intern`, etc.), email addresses, URLs, phone numbers, and decorative lines. If multiple candidates exist, scores them deterministically based on capitalization, token length (1–4 tokens), and entity labels.
- **Organizations & Dates**: Identifies employer and institutional names, associating start dates, end dates, and current employment indicators (`Present`, `Current`).

### Skill Knowledge Base & Context-Aware Matching
`SkillExtractor` references a curated JSON ontology (`src/resumind/data/skills.json`) containing **75 canonical skills** across 8 categories:
1. **Programming Languages**: Python, Java, C++, C, C#, TypeScript, JavaScript, Go, Ruby, Rust, PHP, Swift, Kotlin, HTML, CSS, Bash, R.
2. **Frameworks & Libraries**: React, Angular, Vue.js, Django, Flask, FastAPI, Spring, Express, Node.js.
3. **Machine Learning / AI**: PyTorch, TensorFlow, scikit-learn, Keras, Pandas, NumPy, OpenCV, Natural Language Processing, Machine Learning, Artificial Intelligence.
4. **Data & Databases**: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, Apache Spark, Snowflake, Kafka.
5. **Cloud & Infrastructure**: AWS, Azure, Google Cloud Platform, Docker, Kubernetes, Terraform.
6. **Developer Tools**: Git, GitHub, Linux, CMake, GitHub Actions, Jenkins, REST API, GraphQL, CI/CD.
7. **Management & Methodologies**: Project Management, Agile, Scrum.
8. **Soft Skills**: Leadership, Communication, Teamwork, Collaboration, Problem Solving, Critical Thinking, Time Management, Adaptability, Organizational Skills, Creativity, Conflict Resolution, Decision Making, Presentation Skills, Negotiation, Mentoring.

**Disambiguation & Boundary Protection**:
- Precompiled regex patterns sorted by token length descending ensure `scikit-learn` matches before `C`, and `JavaScript` does not falsely trigger `Java`.
- Short ambiguous tokens (`Go`, `C`, `R`, `Bash`) require technical context (technical sections or keywords like *proficient in*, *developed with*, *programming in*) to prevent false positives on common prose (e.g. *"go further"*, *"in a nutshell"*).

---

## 6. Structured Output Schema

The parser outputs a dictionary adhering to the `ResumeData` Pydantic model:

```json
{
  "metadata": {
    "file_name": "resume.pdf",
    "file_type": "pdf",
    "processing_timestamp": "2026-09-23T22:30:00Z",
    "parser_version": "1.0.0"
  },
  "candidate": {
    "name": "Jane Doe",
    "location": "San Francisco, CA"
  },
  "contact": {
    "emails": ["jane.doe@example.com"],
    "phones": [
      {
        "raw": "+1 (555) 123-4567",
        "normalized": "+15551234567"
      }
    ],
    "linkedin": ["https://linkedin.com/in/janedoe"],
    "github": ["https://github.com/janedoe"],
    "portfolios": ["https://janedoe.dev"],
    "other_urls": []
  },
  "summary": "Senior Software Engineer with 8+ years of experience...",
  "skills": [
    {
      "canonical_name": "Python",
      "category": "Programming Languages",
      "mentions": [
        {
          "raw_text": "Python",
          "match_type": "exact",
          "section": "skills"
        }
      ]
    }
  ],
  "experience": [
    {
      "role": "Senior Software Engineer",
      "organization": "Google",
      "location": "Mountain View, CA",
      "start_date": "Jan 2021",
      "end_date": "Present",
      "is_current": true,
      "description": [
        "Architected distributed data pipelines handling 50k TPS.",
        "Mentored junior developers and led quarterly sprint planning."
      ],
      "skills": ["Python", "Docker", "Kubernetes"]
    }
  ],
  "education": [
    {
      "degree": "B.Sc in Computer Science",
      "institution": "Stanford University",
      "start_date": "2016",
      "end_date": "2020",
      "grade": "GPA: 3.9/4.0"
    }
  ],
  "projects": [
    {
      "name": "Real-time Telemetry Service",
      "description": "High-throughput stream processing application.",
      "technologies": ["Kafka", "Python", "Docker"]
    }
  ],
  "sections": [...],
  "entities": [...],
  "warnings": []
}
```

---

## 7. Installation & Setup

### Requirements
- **Operating System**: Windows, macOS, or Linux (fully verified on Windows 11)
- **Python Version**: Python 3.11+ (tested on Python 3.11.9)

### 1. Clone the Repository
```bash
git clone https://github.com/adarshh025/resumind.git
cd resumind
```

### 2. Create and Activate Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Package and Dependencies
```bash
pip install -e .[dev]
```

### 4. Install spaCy Language Model
```bash
python -m spacy download en_core_web_sm
```

---

## 8. Usage

### A. Standalone CLI
Use the root `parser.py` runner to parse any PDF or DOCX file directly:
```bash
python parser.py path/to/resume.pdf
```
```bash
python parser.py path/to/resume.docx
```

### B. Python Library API
Import `ResumeParser` directly into your application:
```python
from resumind.parser import ResumeParser

parser = ResumeParser()

# Parse resume file
resume = parser.parsefile("tests/fixtures/1._traditional_single-column.pdf")

print(f"Candidate: {resume['candidate']['name']}")
print(f"Email: {resume['contact']['emails']}")

for exp in resume["experience"]:
    print(f"Role: {exp['role']} | Org: {exp['organization']} | Dates: {exp['start_date']} to {exp['end_date']}")

for edu in resume["education"]:
    print(f"Degree: {edu['degree']} | Institution: {edu['institution']}")

print(f"Extracted Skills: {[s['canonical_name'] for s in resume['skills']]}")
```

### C. FastAPI REST Server
Start the REST API server:
```bash
uvicorn resumind.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

**Example HTTP Request**:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/resumes/parse" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@tests/fixtures/1._traditional_single-column.pdf"
```

### D. Interactive Web UI
With the server running, navigate to `http://127.0.0.1:8000/` in any modern web browser to access the drag-and-drop resume analyzer interface.

---

## 9. Verification & Testing

### Running the Full Test Suite
Execute the complete test suite with `pytest`:
```bash
pytest tests/ -v
```

**Test Suite Coverage (95 Tests Total)**:
- `test_adversarial.py` (12 tests): Evaluates candidate name safeguards against table borders (`|---|---|`), decorative dividers (`===`, `---`), raw job titles (`Data Analyst`), contact pipe lines (`David Chen | email | phone`), inline headings, one-line experience/education patterns, and skill ambiguity protection.
- `test_api.py` (6 tests): Evaluates file upload handling, 5 MB file size limit (HTTP 413), unsupported file types (HTTP 415), empty files (HTTP 400), health checks, and JSON response serialization.
- `test_assembly.py` (3 tests): Verifies candidate profile synthesis, one-line and multi-line experience grouping, and degree/institution grouping.
- `test_contact.py` (5 tests): Verifies email extraction, phone validation (excluding dates, ZIPs, and GPAs), phone normalization, URL categorization, and contact deduplication.
- `test_e2e.py` (1 test): End-to-end multi-section extraction pipeline verification.
- `test_ingestion.py` (11 tests): Ingestion factory, PDF text extraction, DOCX paragraph and table parsing, corrupt files, and non-extractable PDF detection.
- `test_layout_fixtures.py` (28 tests): Automated benchmark testing 20 diverse layout PDFs with strict Pydantic schema validation and semantic extraction assertions for candidate names, emails, roles, organizations, degrees, institutions, and skills.
- `test_ner.py` (4 tests): Verifies candidate detection, organization extraction, date extraction, and location identification.
- `test_parser.py` (5 tests): Evaluates `ResumeParser.parsefile()` on valid and invalid files.
- `test_preprocessing.py` (7 tests): Evaluates Unicode NFKC normalization, whitespace collapse, bullet canonicalization, divider removal, and token preservation.
- `test_segmentation.py` (7 tests): Evaluates exact headings, casing scoring, inline headings, duplicate section retention, and unknown section preservation.
- `test_skills.py` (6 tests): Evaluates canonical matching, alias mapping, category assignment, version capture, and context-aware ambiguity resolution.

### Running NLP Quality Evaluation
Run the standalone NLP evaluation script:
```bash
python scripts/evaluate_nlp.py
```

---

## 10. Layout Robustness Benchmark

Resumind includes 20 benchmark resume layouts located in `tests/fixtures/generated_resumes/`:

| Fixture Name | Layout Characteristics | Verification Highlights |
| :--- | :--- | :--- |
| `1._traditional_single-column.pdf` | Classic chronological single-column | Robert Vance; Operations Manager at Apex Logistics; BBA at Univ of Illinois |
| `2._two-column.pdf` | Side-by-side two-column layout | Elena Rostova; Senior Designer at Creativebox |
| `3._minimal_resume.pdf` | Compact, sparse text layout | David Chen; B.A. English Literature at UC Berkeley |
| `4._dense_technical_resume.pdf` | High token density, AWS/IaC keywords | Priya Patel; Principal Cloud Engineer at DataSynergy; AWS, Docker, K8s, Jenkins |
| `5._fresher_resume.pdf` | Entry-level graduate layout | Marcus Johnson; B.S. Computer Science at SUNY (2026); GPA 3.8/4.0 |
| `6._experienced_developer.pdf` | Multi-tier senior engineering history | Sarah Jenkins; Senior Staff Engineer at GlobalFintech Solutions |
| `7._resume_with_no_summary.pdf` | Direct entry into experience section | Michael O'Connor; Regional Sales Director at Horizon Medical Devices; B.S. Marketing at FSU |
| `8._resume_with_no_projects.pdf` | Pure employment and education history | Linda Kravitz; HR Director at SteelWorks; M.S. at Georgetown, B.A. at Maryland |
| `9._resume_with_duplicate_sections.pdf` | Repeated section headers | Alex Mercer; sequential duplicate preservation without data loss |
| `10._resume_with_unusual_headings.pdf` | Non-standard heading labels | Chloe Summers; preserves unknown sections under `unknown` |
| `11._resume_with_aliases.pdf` | Dense alias usage (`JS`, `sklearn`) | Jordan Lee; canonicalizes React, Python, scikit-learn |
| `12._resume_with_multiple_phone_formats.pdf` | Mixed international & national phones | Isabella Rossi; Managing Consultant at Global Partners Ltd. |
| `13._resume_with_tables.pdf` | Table-wrapped content | Thomas Wright; cleanly extracts cells without table-border noise |
| `14._resume_with_unusual_bullets.pdf` | Unicode bullet characters (`▪`, `►`) | Samantha Blake; canonicalizes bullets to standard hyphens |
| `15._resume_with_missing_contact_information.pdf` | Anonymized stealth executive | Victor Sterling; CEO at Undisclosed Manufacturing; MBA at Harvard Business School |
| `16._resume_with_long_experience_history.pdf` | 30-year employment timeline | Arthur Pendelton; 5 distinct chronological positions |
| `17._resume_with_education_first.pdf` | Academic CV layout with education first | Dr. Emily Carter; Ph.D. at MIT, M.S. at Stanford; Postdoc at Broad Institute |
| `18._resume_with_projects_before_experience.pdf` | Portfolio-first layout | Kevin Zhao; Junior Web Developer at AgencyX |
| `19._resume_with_noisy_headers_footers.pdf` | Repetitive page numbers and footers | Jonathan Reed; Senior Counsel at Apex Financial; J.D. at Columbia Law School |
| `20._complex_layout___extraction-stress_case.pdf` | Multi-column, irregular whitespace | Nina Williams; candidate name and 9 technical skills extracted cleanly |

---

## 11. Security & Privacy Considerations

- **100% Local & Offline**: All processing occurs locally on the host machine. No network requests are initiated during parsing.
- **No Data Retention**: The REST API streams uploads directly to OS-managed temporary files (`tempfile.mkstemp`) and guarantees immediate deletion via unconditional `finally: os.unlink()` hooks.
- **Resource Exhaustion Safeguards**: A strict 5 MB streaming size limit is enforced at the ASGI level, rejecting oversized payloads (`HTTP 413`) before memory buffers can be saturated.
- **Path Traversal Protection**: Uploaded file names are strictly sanitized. Temporary storage uses cryptographically random OS descriptors.
- **XSS-Safe Frontend**: The web UI enforces strict HTML character escaping on all dynamic extraction content before rendering to the DOM.
- **Zero Credentials / Private Data**: No API keys, credentials, or private personal resumes are checked into the repository. All test fixtures are synthetic.

---

## 12. Known Limitations & Technical Scope

- **Scanned & Image-Only PDFs**: Resumind processes extractable text streams only. PDFs consisting purely of rasterized images safely report `status: "TEXT_NOT_EXTRACTABLE"`. Optical Character Recognition (OCR) engines like Tesseract are deliberately excluded to avoid heavy external binary dependencies.
- **Custom NER Fine-Tuning**: In alignment with technical honesty, Resumind uses spaCy's pretrained `en_core_web_sm` model augmented by deterministic domain rules rather than a custom fine-tuned NER model. This keeps the installation lightweight and reproducible without requiring GPU hardware or multi-gigabyte model weights.
- **Multi-Column Flow Heuristics**: Severely non-standard or artistic multi-column PDFs may occasionally experience fragmented reading orders based on `pdfminer.six` geometric flow algorithms.
- **Language**: Rule sets, section aliases, and spaCy models are configured exclusively for English-language resumes.

---

## 13. Repository Structure

```
resumind/
├── .github/                      # GitHub issue templates and workflows
├── docs/                         # Engineering specifications and reports
│   ├── architecture.md           # Module architecture and data flow
│   ├── evaluation.md             # NLP precision and security evaluation report
│   ├── PROJECT_CONTRACT.md       # Project identity and technological rules
│   ├── release-readiness.md      # Release readiness and verification audit
│   ├── requirements-traceability.md # Persevex requirement-by-requirement traceability
│   └── testing-baseline.md       # Testing environment and execution baseline
├── parser.py                     # Standalone CLI and evaluator re-export wrapper
├── pyproject.toml                # PEP 621 package metadata and dependencies
├── README.md                     # Project documentation
├── LICENSE                       # MIT License
├── scripts/
│   ├── evaluate_nlp.py           # NLP evaluation benchmark script
│   └── generate_fixtures.py      # Synthetic PDF fixture generator
├── src/
│   └── resumind/
│       ├── __init__.py           # Package root (exposes ResumeParser, ResumeCleaner, Sectionizer)
│       ├── parser.py             # Core ResumeParser implementation
│       ├── app/                  # FastAPI REST service and web frontend
│       │   ├── api/routes.py     # REST endpoints (/api/v1/resumes/parse)
│       │   ├── main.py           # FastAPI application entrypoint
│       │   ├── services/upload.py # Secure streaming file upload handler
│       │   └── static/           # Lightweight web UI (HTML, CSS, JS)
│       ├── assembly/
│       │   └── assembler.py      # Unified model assembly (role/org and degree/inst parsing)
│       ├── data/
│       │   └── skills.json       # 75-skill canonical ontology with aliases
│       ├── extraction/
│       │   ├── contact.py        # Contact extractor (email, phone, URL)
│       │   └── skills.py         # Context-aware skill extractor
│       ├── ingestion/
│       │   ├── base.py           # Extractor interfaces and format detection
│       │   ├── docx.py           # python-docx document extractor
│       │   ├── factory.py        # Extractor factory pattern
│       │   └── pdf.py            # pdfminer.six document extractor
│       ├── models/
│       │   └── resume.py         # Pydantic data schemas (ResumeData, Experience, Education)
│       ├── nlp/
│       │   └── ner.py            # Semantic entity layer (spaCy NER + candidate scoring)
│       ├── preprocessing/
│       │   └── cleaner.py        # Text cleaning, normalization, divider removal
│       └── segmentation/
│           ├── models.py         # SectionBlock schema
│           └── sectionizer.py    # Section boundary and inline heading analyzer
└── tests/                        # 95 automated test cases
    ├── conftest.py               # Shared test fixtures
    ├── test_adversarial.py       # Adversarial safeguards and regression tests
    ├── test_api.py               # FastAPI REST endpoint and upload tests
    ├── test_assembly.py          # ResumeAssembler unit tests
    ├── test_contact.py           # Contact extraction unit tests
    ├── test_e2e.py               # Full end-to-end extraction test
    ├── test_ingestion.py         # PDF and DOCX ingestion tests
    ├── test_layout_fixtures.py   # 20 layout fixtures benchmark (schema & semantic tests)
    ├── test_ner.py               # Entity recognition unit tests
    ├── test_parser.py            # ResumeParser class tests
    ├── test_preprocessing.py     # Text cleaner unit tests
    ├── test_segmentation.py      # Sectionizer unit tests
    ├── test_skills.py            # Skill ontology and alias resolution tests
    └── fixtures/                 # Test files and 20 generated layout benchmark PDFs
```

---

## 14. License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

```
Copyright (c) 2026 Adarsh Aher
```
