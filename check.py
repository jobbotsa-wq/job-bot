#!/usr/bin/env python3
"""
Validación pre-commit: sintaxis, imports y tests.
Uso: python check.py
Retorna exit code 0 si todo OK, 1 si hay errores.
"""
import subprocess
import sys
import os


def run(cmd, label):
    print(f"\n{'-'*50}")
    print(f"  {label}")
    print(f"{'-'*50}")
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    ok = result.returncode == 0
    print(f"  {'[OK]' if ok else '[FALLO]'}")
    return ok


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    results = []

    # 1. Verificar sintaxis de todos los .py
    results.append(run(
        'python -m py_compile '
        'main.py '
        'cv_review.py '
        'src/core/orchestrator.py '
        'src/core/cv_parser.py '
        'src/core/job_matcher.py '
        'src/core/cv_reviewer.py '
        'src/platforms/base_platform.py '
        'src/platforms/linkedin/login.py '
        'src/platforms/linkedin/job_search.py '
        'src/platforms/linkedin/easy_apply.py '
        'src/notifier/email_notifier.py '
        'src/storage/db.py',
        "Verificando sintaxis Python"
    ))

    # 2. Verificar imports (sin ejecutar lógica externa)
    results.append(run(
        'python -c "'
        'import yaml; import sqlite3; import smtplib; '
        'import pdfplumber; '
        'print(\'Dependencias core OK\')'
        '"',
        "Verificando dependencias instaladas"
    ))

    # 3. Tests unitarios (si existen)
    if os.path.exists("tests"):
        results.append(run("python -m pytest tests/ -v --tb=short", "Ejecutando tests"))
    else:
        print("\n  [Tests] No hay carpeta tests/ — omitiendo")

    # Resultado final
    print(f"\n{'='*50}")
    if all(results):
        print("  VALIDACION EXITOSA -- listo para commit")
        sys.exit(0)
    else:
        print("  VALIDACION FALLIDA -- corregir antes de hacer commit")
        sys.exit(1)


if __name__ == "__main__":
    main()
