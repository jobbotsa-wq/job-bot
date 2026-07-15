#!/usr/bin/env python3
"""
Guardias de seguridad para el repo. Uso: python tools/security_guards.py

Este repo ejecuta un workflow de GitHub Actions con secrets sensibles
(LinkedIn, Gmail, Gemini) y un hook de Claude Code que corre automaticamente
sin pedir confirmacion. Estas guardias hacen RUIDOSO un cambio peligroso, no
imposible: si un PR necesita ensanchar algo de esto a proposito, debe
actualizar el allowlist de este mismo archivo en el mismo diff.

Chequeos:
1. .gitignore — las reglas de datos personales deben seguir presentes.
   Ya hubo una regresion real de esto (cv/*.pdf vs cv.pdf) detectada
   manualmente; esta guardia la habria atrapado sola.
2. .claude/settings.json — si existe permissions.allow, cada entrada debe
   estar en el allowlist revisado de abajo. Job-bot no usa permissions.allow
   hoy, pero si alguien lo agrega (ej. "Bash(*)") esto lo bloquea.

Nota: .claude/settings.json tambien puede tener "hooks", que se ejecutan
automaticamente sin prompt. Este script no audita el contenido de los hooks
(fuera de alcance por ahora) - solo permissions.allow y .gitignore.

Stdlib only. Exit 0 si todo bien, 1 con lista de errores si no.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []

# Ninguna entrada pre-aprobada por ahora. Si un PR agrega permissions.allow
# a proposito, debe agregar la entrada exacta aqui en el mismo diff.
ALLOWED_PERMISSIONS: set[str] = set()

REQUIRED_IGNORE_RULES = [
    "users/*/credentials.yaml",
    "users/*/cv.pdf",
    "users/*/cv_xyz_review.md",
    "ACCOUNTS.txt",
    "data/*.db",
    "logs/",
]


def check_gitignore() -> None:
    path = ROOT / ".gitignore"
    try:
        rules = {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}
    except OSError as exc:
        errors.append(f".gitignore: illegible: {exc}")
        return
    for rule in REQUIRED_IGNORE_RULES:
        if rule not in rules:
            errors.append(
                f".gitignore: falta la regla de datos personales: {rule!r}. "
                "Si se renombro o movio a proposito, actualiza REQUIRED_IGNORE_RULES "
                "en tools/security_guards.py en el mismo PR."
            )


def check_claude_permissions() -> None:
    path = ROOT / ".claude" / "settings.json"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f".claude/settings.json: illegible o JSON invalido: {exc}")
        return
    if not isinstance(data, dict):
        errors.append(".claude/settings.json: el valor raiz debe ser un objeto")
        return
    permissions = data.get("permissions", {})
    if not permissions:
        return
    if not isinstance(permissions, dict):
        errors.append(".claude/settings.json: permissions debe ser un objeto")
        return
    allow = permissions.get("allow", [])
    if not isinstance(allow, list) or not all(isinstance(e, str) for e in allow):
        errors.append(".claude/settings.json: permissions.allow debe ser una lista de strings")
        return
    for entry in allow:
        if entry not in ALLOWED_PERMISSIONS:
            errors.append(
                f".claude/settings.json: permiso fuera del allowlist revisado: {entry!r}. "
                "Un permiso en 'allow' se auto-aprueba sin preguntar. Si es intencional, "
                "agregalo a ALLOWED_PERMISSIONS en tools/security_guards.py en el mismo PR."
            )


def main() -> int:
    check_gitignore()
    check_claude_permissions()
    if errors:
        print(f"security_guards: {len(errors)} fallo(s)")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("security_guards: OK (.gitignore, permissions.allow)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
