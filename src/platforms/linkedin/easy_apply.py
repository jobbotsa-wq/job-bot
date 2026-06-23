import time
import random
from playwright.sync_api import Page


def apply_easy_apply(page: Page, job: dict, profile: dict) -> dict:
    """Aplica a una oferta con Easy Apply de LinkedIn."""
    result = {"status": "skipped", "notes": ""}

    try:
        page.goto(job["url"], timeout=30000)
        time.sleep(random.uniform(2, 4))

        # Verificar que tiene Easy Apply
        easy_btn = page.query_selector(".jobs-apply-button--top-card")
        if not easy_btn:
            result["notes"] = "No tiene Easy Apply"
            return result

        btn_text = easy_btn.inner_text().lower()
        if "easy apply" not in btn_text and "solicitud sencilla" not in btn_text:
            result["notes"] = "Botón no es Easy Apply"
            return result

        easy_btn.click()
        time.sleep(random.uniform(2, 3))

        # Navegar por el formulario (máximo 5 pasos)
        for step in range(5):
            # Buscar botón "Next", "Review" o "Submit"
            next_btn = page.query_selector("button[aria-label='Continue to next step']")
            review_btn = page.query_selector("button[aria-label='Review your application']")
            submit_btn = page.query_selector("button[aria-label='Submit application']")

            if submit_btn:
                submit_btn.click()
                time.sleep(random.uniform(2, 3))
                result["status"] = "applied"
                result["notes"] = "Easy Apply completado"
                print(f"[LinkedIn] ✓ Aplicado: {job['title']} en {job['company']}")
                break
            elif review_btn:
                review_btn.click()
                time.sleep(random.uniform(1, 2))
            elif next_btn:
                next_btn.click()
                time.sleep(random.uniform(1, 2))
            else:
                result["notes"] = "Formulario requiere información adicional"
                # Cerrar modal
                close_btn = page.query_selector("button[aria-label='Dismiss']")
                if close_btn:
                    close_btn.click()
                break

        time.sleep(random.uniform(3, 6))

    except Exception as e:
        result["status"] = "error"
        result["notes"] = str(e)
        print(f"[LinkedIn] Error aplicando a {job.get('title')}: {e}")

    return result
