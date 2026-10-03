import re
import pdfplumber
import docx


def extract_text(path):
    ext = path.rsplit(".", 1)[-1].lower()
    text = ""
    if ext == "pdf":
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
    elif ext == "docx":
        d = docx.Document(path)
        text = "\n".join(p.text for p in d.paragraphs)
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    return text.strip()


def extract_contact(text):
    email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    phone = re.search(r"(\+?\d[\d\s\-]{8,}\d)", text)
    linkedin = re.search(r"linkedin\.com/[\w\-/]+", text, re.I)
    github = re.search(r"github\.com/[\w\-/]+", text, re.I)
    first_line = next((l.strip() for l in text.splitlines() if l.strip()), "Candidate")
    return {
        "name": first_line[:40],
        "email": email.group(0) if email else None,
        "phone": phone.group(0).strip() if phone else None,
        "linkedin": linkedin.group(0) if linkedin else None,
        "github": github.group(0) if github else None,
    }