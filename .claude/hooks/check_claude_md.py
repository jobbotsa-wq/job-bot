#!/usr/bin/env python3
"""
Stop hook — job-bot.
Si el ultimo commit toco codigo/config/deps sin tocar CLAUDE.md, bloquea
el fin del turno y pide actualizar CLAUDE.md (ver seccion "Que actualizar
en este archivo" del propio CLAUDE.md).
"""
import json
import re
import subprocess
import sys

TRIGGER_PATTERNS = [
    r"^src/",
    r"^requirements\.txt$",
    r"^config/settings\.yaml$",
    r"^\.github/workflows/",
    r"^users/.*/profile\.yaml$",
    r"^main\.py$",
]


def sh(*args):
    result = subprocess.run(args, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def main():
    if sh("git", "rev-parse", "--is-inside-work-tree") != "true":
        return

    files = [f for f in sh("git", "diff", "--name-only", "HEAD~1", "HEAD").splitlines() if f]
    if not files or "CLAUDE.md" in files:
        return

    triggers = [f for f in files if any(re.match(p, f) for p in TRIGGER_PATTERNS)]
    if not triggers:
        return

    reason = (
        "El ultimo commit modifico archivos sin actualizar CLAUDE.md: "
        + ", ".join(triggers)
        + ". Revisa la seccion 'Que actualizar en este archivo' de CLAUDE.md "
        "(nuevas dependencias, cambios de modelo IA, nuevos campos, cambios en el "
        "flujo del orchestrator, etc.) y agrega una entrada si aplica. Si aplica, "
        "actualiza CLAUDE.md y sigue la regla de git del proyecto (check.py -> commit -> push)."
    )
    print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    main()
