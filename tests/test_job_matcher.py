import sys, os, json, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_score_json_parse():
    """Verifica que el parser de JSON de Gemini funciona con texto extra."""
    raw = 'Aquí está el resultado: {"score": 85, "reason": "Buen match", "apply": true} fin.'
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    assert match, "Debe encontrar JSON en el texto"
    data = json.loads(match.group())
    assert data["score"] == 85
    assert data["apply"] is True
    print("✓ test_score_json_parse OK")


def test_score_json_invalid():
    """Verifica que un texto sin JSON retorna valores seguros."""
    raw = "No puedo procesar esto ahora."
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    result = json.loads(match.group()) if match else {"score": 0, "reason": "Error", "apply": False}
    assert result["score"] == 0
    assert result["apply"] is False
    print("✓ test_score_json_invalid OK")


if __name__ == "__main__":
    test_score_json_parse()
    test_score_json_invalid()
    print("\nTodos los tests pasaron.")
