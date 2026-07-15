import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.cv_reviewer import build_xyz_prompt, generate_xyz_review


def test_prompt_forbids_inventing_metrics():
    """El prompt debe instruir explicitamente a no inventar metricas."""
    prompt = build_xyz_prompt("Lidere el equipo de ventas.")
    assert "nunca inventes" in prompt.lower()
    assert "FALTA METRICA" in prompt
    print("✓ test_prompt_forbids_inventing_metrics OK")


def test_prompt_includes_cv_text():
    """El texto del CV debe llegar completo al prompt."""
    cv_text = "Aumente las ventas en 25% lanzando una nueva linea de negocio."
    prompt = build_xyz_prompt(cv_text)
    assert cv_text in prompt
    print("✓ test_prompt_includes_cv_text OK")


def test_generate_xyz_review_empty_cv():
    """CV vacio no debe llamar al modelo ni fallar."""
    result = generate_xyz_review(model=None, cv_text="   ")
    assert "no se puede" in result.lower() or "no se encontro" in result.lower()
    print("✓ test_generate_xyz_review_empty_cv OK")


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModel:
    def generate_content(self, prompt):
        return _FakeResponse("## Vinetas reescritas en formato XYZ\n...")


def test_generate_xyz_review_returns_model_text():
    result = generate_xyz_review(model=_FakeModel(), cv_text="Lidere un equipo de 5 personas.")
    assert "Vinetas reescritas" in result
    print("✓ test_generate_xyz_review_returns_model_text OK")


if __name__ == "__main__":
    test_prompt_forbids_inventing_metrics()
    test_prompt_includes_cv_text()
    test_generate_xyz_review_empty_cv()
    test_generate_xyz_review_returns_model_text()
    print("\nTodos los tests pasaron.")
