import time
import random
import logging
from playwright.sync_api import Page

logger = logging.getLogger("jobbot")


def apply_easy_apply(page: Page, job: dict, profile: dict) -> dict:
    title = job.get("title", "sin titulo")
    company = job.get("company", "sin empresa")
    result = {"status": "skipped", "notes": ""}

    logger.info(f"Intentando Easy Apply: '{title}' @ {company}")
    logger.debug(f"URL oferta: {job.get('url', '')}")

    try:
        page.goto(job["url"], timeout=30000)
        time.sleep(random.uniform(2, 4))
        logger.debug(f"Pagina cargada — URL actual: {page.url}")

        easy_btn = page.query_selector(".jobs-apply-button--top-card")
        if not easy_btn:
            result["notes"] = "No tiene boton Easy Apply"
            logger.warning(f"Sin boton Easy Apply: '{title}' — oferta puede ser externa")
            return result

        btn_text = easy_btn.inner_text().lower()
        logger.debug(f"Texto del boton: '{btn_text}'")

        if "easy apply" not in btn_text and "solicitud sencilla" not in btn_text:
            result["notes"] = "Boton no es Easy Apply (link externo)"
            logger.warning(f"Boton externo detectado en '{title}': '{btn_text}'")
            return result

        logger.debug("Haciendo clic en Easy Apply")
        easy_btn.click()
        time.sleep(random.uniform(2, 3))

        for step in range(1, 6):
            logger.debug(f"Paso {step}/5 del formulario Easy Apply")
            next_btn = page.query_selector("button[aria-label='Continue to next step']")
            review_btn = page.query_selector("button[aria-label='Review your application']")
            submit_btn = page.query_selector("button[aria-label='Submit application']")

            if submit_btn:
                logger.debug("Boton Submit encontrado — enviando aplicacion")
                submit_btn.click()
                time.sleep(random.uniform(2, 3))
                result["status"] = "applied"
                result["notes"] = f"Easy Apply completado en {step} pasos"
                logger.info(f"APLICACION ENVIADA: '{title}' @ {company} ({step} pasos)")
                break
            elif review_btn:
                logger.debug(f"Paso {step}: clic en Review")
                review_btn.click()
                time.sleep(random.uniform(1, 2))
            elif next_btn:
                logger.debug(f"Paso {step}: clic en Next")
                next_btn.click()
                time.sleep(random.uniform(1, 2))
            else:
                result["notes"] = "Formulario requiere datos adicionales — no completado"
                logger.warning(
                    f"Formulario bloqueado en paso {step} para '{title}' — "
                    f"requiere informacion manual (pregunta personalizada o campo vacio)"
                )
                close_btn = page.query_selector("button[aria-label='Dismiss']")
                if close_btn:
                    close_btn.click()
                    logger.debug("Modal cerrado")
                break

        time.sleep(random.uniform(3, 6))

    except Exception as e:
        result["status"] = "error"
        result["notes"] = str(e)
        logger.error(f"Excepcion aplicando a '{title}': {e}", exc_info=True)

    logger.debug(f"Resultado Easy Apply '{title}': status={result['status']} | {result['notes']}")
    return result
