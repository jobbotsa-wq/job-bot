#!/usr/bin/env python3
"""
Genera un reporte de sugerencias en formato XYZ para el CV de un usuario.
Uso: python cv_review.py [user_id]  (default: user_001)

No modifica el CV ni sube nada a LinkedIn. Es solo un reporte de sugerencias
que el usuario revisa y aplica manualmente a su CV real.
"""
import sys
import os
from pathlib import Path

from src.logger import setup_logger
from src.core.orchestrator import load_yaml, load_credentials
from src.core.cv_parser import extract_cv_text
from src.core.job_matcher import setup_gemini
from src.core.cv_reviewer import generate_xyz_review


def main():
    user_id = sys.argv[1] if len(sys.argv) > 1 else "user_001"
    base = Path(__file__).parent
    user_dir = base / "users" / user_id

    logger = setup_logger(user_id)

    profile = load_yaml(str(user_dir / "profile.yaml"))
    credentials = load_credentials(str(user_dir / "credentials.yaml"))

    cv_path = os.path.join(str(user_dir), profile.get("personal", {}).get("cv_path", "cv.pdf"))
    cv_text = extract_cv_text(cv_path)
    if not cv_text:
        print(f"No se pudo leer el CV en {cv_path}")
        sys.exit(1)

    gemini_key = credentials.get("ai", {}).get("gemini_api_key", "")
    model = setup_gemini(gemini_key)
    if not model:
        print("Gemini no configurado en credentials.yaml — no se puede generar la revision.")
        sys.exit(1)

    review = generate_xyz_review(model, cv_text)

    out_path = user_dir / "cv_xyz_review.md"
    out_path.write_text(review, encoding="utf-8")
    logger.info(f"Revision XYZ guardada en {out_path}")
    print(f"Revision guardada en: {out_path}")
    print("Revisala y aplica manualmente lo que te sirva a tu CV real. Esto NO sube nada a LinkedIn.")


if __name__ == "__main__":
    main()
