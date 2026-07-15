import logging

logger = logging.getLogger("jobbot")

XYZ_PROMPT_TEMPLATE = """
Eres un experto en redaccion de curriculums. Vas a reescribir las vinetas de
logros de la seccion de experiencia laboral usando el formato XYZ recomendado
por reclutadores de Google (Laszlo Bock): "Logre [X], medido por [Y], mediante [Z]".

- X = el logro o resultado
- Y = el dato medible que lo respalda (porcentaje, monto, cantidad, tiempo, etc.)
- Z = la accion o metodo usado para lograrlo

REGLA INQUEBRANTABLE: nunca inventes, estimes ni asumas una metrica (Y) que no
este ya presente literalmente en el texto del CV de abajo. Si una vinieta
describe un logro o responsabilidad pero el CV no trae un numero para
respaldarla, NO la reescribas en formato XYZ. En su lugar, deja la vinieta
original tal cual y marcala como "FALTA METRICA" explicando que dato medible
la fortaleceria (sin inventar el valor).

CV DEL CANDIDATO:
{cv_text}

Responde en markdown con exactamente estas dos secciones:

## Vinetas reescritas en formato XYZ
(Solo las vinetas que ya tenian una metrica en el CV original. Cada una como:
original -> reescrita)

## Vinetas que necesitan una metrica
(Vinetas sin dato medible en el CV original. Cada una: la vinieta original,
seguida de una sugerencia del TIPO de metrica que la fortaleceria, sin
inventar el numero)
"""


def build_xyz_prompt(cv_text: str) -> str:
    return XYZ_PROMPT_TEMPLATE.format(cv_text=cv_text[:6000])


def generate_xyz_review(model, cv_text: str) -> str:
    if not cv_text.strip():
        logger.warning("CV vacio — no se puede generar revision XYZ")
        return "No se encontro texto de CV para analizar."

    logger.info("Generando revision de CV en formato XYZ")
    prompt = build_xyz_prompt(cv_text)
    try:
        response = model.generate_content(prompt)
        review = response.text.strip()
        logger.info(f"Revision XYZ generada ({len(review)} caracteres)")
        return review
    except Exception as e:
        logger.error(f"Error generando revision XYZ: {e}", exc_info=True)
        return "Error al generar la revision con IA. Revisa los logs para mas detalle."
