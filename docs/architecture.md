# Resumind: Architecture Specification

## 1. Architectural Philosophy
Resumind is engineered as a decoupled, multi-layered data extraction pipeline. The core NLP and extraction engine operates independently of presentation frameworks, allowing seamless execution as an embedded Python library, a command-line utility, or a containerized REST microservice.

---

## 2. Module Responsibilities

### `resumind.ingestion`
Handles binary file validation, format detection, and text stream extraction.
- **Factory Pattern**: `get_extractor(filepath)` returns a format-specific `DocumentExtractor`.
- **`PdfExtractor`**: Uses `pdfminer.six` with configured `LAParams` to extract flowing text while respecting line breaks. Flags unextractable/scanned documents gracefully.
- **`DocxExtractor`**: Uses `python-docx` to iterate through document paragraphs and table cells, normalizing layout boundaries.
- **Error Handling**: Missing files trigger `FileNotFoundError`; unsupported extensions trigger `ValueError`.

### `resumind.preprocessing`
Performs deterministic text normalization via `ResumeCleaner`.
- **Unicode Normalization**: Applies NFKC normalization to resolve compatibility characters and ligatures.
- **Control Character Filtering**: Removes invisible control characters while preserving essential whitespace (`\n`, `\t`).
- **Divider and Table Border Filtration**: Filters out decorative horizontal rules (`---`, `===`, `___`, `+------------------+`, `---------------~----`) and Markdown table dividers (`|---|---|`).
- **Token Protection**: Preserves technical language tokens such as `C++`, `C#`, `Node.js`, `CI/CD`, and `A/B Testing`.
- **Bullet Canonicalization**: Normalizes disparate bullet characters (`•`, `*`, `▪`, `►`) to standard hyphens (`-`).

### `resumind.segmentation`
Partitions cleaned document text into semantic section blocks via `Sectionizer`.
- **Implicit Contact Header**: Captures initial lines prior to any formal section heading into `contact_header` with confidence `1.0`.
- **Heading Detection**: Evaluates lines against alias tables with length constraints (`len <= 50`).
- **Inline Headings**: Recognizes inline section prefixes (e.g. `Experience: Principal Engineer at Google`) and transfers the remainder into the section content.
- **Confidence Scoring**: Exact uppercase matches score `0.95`; title case scores `0.85`; lowercase/mixed scores `0.70`.
- **Unknown Section Handling**: Preserves non-standard section titles (`PUBLICATIONS`, `AWARDS`) under `unknown` (`0.60` confidence) rather than dropping content.
- **Duplicate Preservation**: Retains multiple blocks of the same type across multi-page resumes sequentially.

### `resumind.extraction`
Orchestrates domain-specific information extraction.
- **`ContactExtractor`**: Uses high-precision regex to extract emails, phone numbers, and URLs (LinkedIn, GitHub, portfolios).
  - Phone normalization strips formatting, preserves explicit `+` prefixes, normalizes 11-digit NANP numbers, and leaves ambiguous national numbers intact.
  - URL normalization enforces standard `https://` protocol prefixes.
- **`SkillExtractor`**: Context-aware skill extraction engine backed by `src/resumind/data/skills.json` (75 canonical skills).
  - Precompiles regexes sorted by length descending for longest-match-first matching.
  - Resolves aliases (e.g. `React.js` -> `React`, `sklearn` -> `scikit-learn`, `HTML5` -> `HTML`).
  - Implements ambiguity guards to prevent false positives for short tokens (`Go`, `C`, `R`, `Bash`) outside technical contexts.

### `resumind.nlp`
The Semantic Entity Layer (`SemanticEntityExtractor`).
- Utilizes spaCy's pretrained `en_core_web_sm` pipeline.
- Extracts `CANDIDATE` (filtered `PERSON` entities from `contact_header`), `ORGANIZATION`, `DATE`, and `LOCATION` entities.
- Enforces strict candidate name filters against decorative borders, table cells, emails, URLs, and common job titles.

### `resumind.assembly`
Synthesizes all disjointed extractions into the canonical `ResumeData` model via `ResumeAssembler`.
- **Candidate Assembly**: Selects NER-validated candidate or executes robust fallback filtering.
- **Experience Assembly**: Parses single-line (`Role at Company`, `Company - Role`, `Role | Company`, `Role @ Company`) and multi-line structures. Associates roles, organizations, dates, current employment flags, descriptions, and binds referenced skills.
- **Education Assembly**: Splits degree titles (`B.Sc in Computer Science`) and institutions (`Stanford University`) without dropping either field. Captures GPA/grades and graduation dates.
- **Project Assembly**: Groups project titles, bullet descriptions, and technology mentions.

### `resumind.models`
Defines canonical data schemas using Pydantic:
- `Metadata`, `CandidateProfile`, `ContactInfo`, `Experience`, `Education`, `Project`, `CanonicalSkill`, `Entity`, `ResumeData`.

### `resumind.app`
Presentation layer built with FastAPI:
- Exposes `POST /api/v1/resumes/parse` supporting multipart file uploads.
- Serves lightweight, professional static web interface (`index.html`, `style.css`, `app.js`).
- Enforces security controls: 5 MB streaming size limit, extension validation, safe temporary file allocation, and unconditional cleanup in `finally` blocks.

---

## 3. Data Flow Diagram

```
Resume Document (.pdf, .docx)
               │
               ▼
       DocumentExtractor
               │ (raw_text)
               ▼
         ResumeCleaner
               │ (cleaned_text)
               ▼
          Sectionizer
               │ (SectionBlocks)
               ├─────────────────────────────────────────┐
               ▼                                         ▼
        ContactExtractor                         SkillExtractor
    (Emails, Phones, URLs)                  (75 Skills + Aliases)
               │                                         │
               ├─────────────────────────────────────────┤
               ▼                                         ▼
     SemanticEntityExtractor                      ResumeAssembler
  (Candidate, Org, Date, Loc)                 (Role/Org, Deg/Inst Split)
               │                                         │
               └────────────────────┬────────────────────┘
                                    ▼
                               ResumeData
                           (Structured JSON)
```
