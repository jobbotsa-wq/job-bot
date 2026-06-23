import pdfplumber
import os


def extract_cv_text(cv_path: str) -> str:
    if not os.path.exists(cv_path):
        print(f"[CV] Archivo no encontrado: {cv_path}")
        return ""
    text = ""
    with pdfplumber.open(cv_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()
