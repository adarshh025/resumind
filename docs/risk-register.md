# Resumind Risk Register

This document explicitly identifies known risks, edge-cases, and limitations of the Resumind architecture. None of these limitations are hidden; they are engineering tradeoffs made to ensure security, offline capability, and determinism.

| Risk ID | Category | Description | Probability | Impact | Mitigation / Status |
|---------|----------|-------------|-------------|--------|---------------------|
| RSK-01 | Parsing | **Scanned (Image-only) PDFs**: System lacks OCR capabilities and cannot extract text from raw images. | Medium | High | **Limitation Documented**. The ingestion pipeline checks for empty byte yields and explicitly returns `TEXT_NOT_EXTRACTABLE` rather than failing silently or hallucinating data. |
| RSK-02 | Accuracy | **Two-Column PDF Ordering**: The `pdfminer.six` library reconstructs reading order heuristically. Highly complex two-column layouts might merge lines incorrectly. | High | Medium | **Limitation Documented**. The parser relies on robust section headings to recover structural intent, but some line merging may still occur. |
| RSK-03 | Privacy | **Residual Temporary Files**: API crashes during PDF processing could theoretically strand temporary files on disk. | Low | Low | **Mitigated**. The FastAPI endpoint enforces a strict `try...finally` block that guarantees `os.unlink()` runs unconditionally. |
| RSK-04 | Security | **Resource Exhaustion (DOS)**: Gigantic files could exhaust server memory if read fully into memory. | Low | High | **Mitigated**. The API reads the incoming stream in 8KB chunks and explicitly throws `HTTP 413 File Too Large` if it crosses 5MB, protecting the event loop. |
| RSK-05 | Accuracy | **Multilingual Resumes**: NLP models (`en_core_web_sm`) are trained exclusively on English data. | High | Medium | **Limitation Documented**. Will fail to identify entities correctly on non-English resumes. |
| RSK-06 | Scalability| **Synchronous Event Loop Blocking**: The NLP execution happens on the main thread, blocking FastAPI from handling simultaneous requests. | High | High (at scale) | **Limitation Documented**. For true production deployment at scale, `ResumeParser.parsefile()` must be offloaded to a `ThreadPoolExecutor` or Celery worker. |
| RSK-07 | Accuracy | **Entity Collision**: Ambiguous terms (e.g. "Apple" or "Amazon") might be misinterpreted as skills vs companies depending on casing and context. | Medium | Low | **Mitigated**. The explicit skill extraction uses word boundaries (`\b`) and strictly matches predefined ontologies, avoiding generic inferences. |
