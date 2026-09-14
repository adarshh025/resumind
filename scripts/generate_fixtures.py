import os
import docx
from fpdf import FPDF
from pathlib import Path

FIXTURE_DIR = Path("tests/fixtures")
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

def make_pdf(filename, text_pages):
    pdf = FPDF()
    for text in text_pages:
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=text)
    pdf.output(FIXTURE_DIR / filename)

def make_docx(filename, paragraphs, tables=None):
    doc = docx.Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    if tables:
        for t_data in tables:
            table = doc.add_table(rows=len(t_data), cols=len(t_data[0]))
            for i, row in enumerate(t_data):
                for j, cell_text in enumerate(row):
                    table.cell(i, j).text = cell_text
    doc.save(FIXTURE_DIR / filename)

# Fixture A: Simple one page text resume
make_pdf("fixture_a.pdf", ["Adarsh Aher\nSoftware Engineer\nExperience: 5 years"])
make_docx("fixture_a.docx", ["Adarsh Aher", "Software Engineer", "Experience: 5 years"])

# Fixture B: Two page resume
make_pdf("fixture_b.pdf", ["Page 1\nContact Info", "Page 2\nEducation"])
make_docx("fixture_b.docx", ["Page 1", "Contact Info"])

# Fixture C: Resume with tables (docx only)
make_docx("fixture_c.docx", ["Summary"], tables=[
    [["Skill", "Level"], ["Python", "Expert"], ["FastAPI", "Advanced"]]
])

# Fixture D: Empty PDF/DOCX
make_pdf("fixture_empty.pdf", [""])
make_docx("fixture_empty.docx", [])

# Fixture E: Corrupt files
(FIXTURE_DIR / "corrupt.pdf").write_text("This is not a pdf")
(FIXTURE_DIR / "corrupt.docx").write_text("This is not a docx")

print("Fixtures generated.")
