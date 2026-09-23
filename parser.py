"""
Resumind root parser compatibility module.

Re-exports ResumeParser from the core resumind package for evaluator
and script compatibility (e.g. `from parser import ResumeParser`).
Provides a standalone CLI for direct execution: `python parser.py <filepath>`.
"""
import sys
import json
from pathlib import Path

# Re-export core implementation as the single source of truth
from resumind.parser import ResumeParser

__all__ = ["ResumeParser"]


def main():
    """Minimal standalone CLI to parse a resume file and print structured JSON."""
    if len(sys.argv) < 2:
        print("Usage: python parser.py <path_to_resume.[pdf|docx]>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    path_obj = Path(filepath)

    if not path_obj.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    try:
        parser = ResumeParser()
        result = parser.parsefile(str(path_obj))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error parsing resume: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
