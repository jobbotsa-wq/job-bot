import time
import random
import logging
from playwright.sync_api import Page

logger = logging.getLogger("jobbot")


def linkedin_login(page: Page, email: str, password: str) -> bool:
    logger.info(f"Iniciando login en LinkedIn con cuenta: {email}")
    try:
        logger.debug("Navegando a pagina de login de LinkedIn")
        page.goto("https://www.linkedin.com/login", timeout=30000)
        time.sleep(random.uniform(2, 4))
        logger.debug(f"URL actual tras navegar: {page.url}")

        logger.debug("Ingresando credenciales")
        page.fill("#username", email)
        time.sleep(random.uniform(0.5, 1.5))
        page.fill("#password", password)
        time.sleep(random.uniform(0.5, 1.5))

        logger.debug("Haciendo clic en Submit")
        page.click('[type="submit"]')
        time.sleep(random.uniform(3, 5))

        current_url = page.url
        logger.debug(f"URL post-login: {current_url}")

        if "feed" in current_url or "mynetwork" in current_url:
            logger.info("Login exitoso en LinkedIn")
            return True

        if "checkpoint" in current_url or "challenge" in current_url:
            logger.error(
                f"LinkedIn requiere verificacion manual (CAPTCHA o 2FA). "
                f"URL: {current_url} — revisar la cuenta manualmente"
            )
            return False

        logger.error(f"Login fallido — URL inesperada: {current_url}")
        return False

    except Exception as e:
        logger.error(f"Excepcion durante login en LinkedIn: {e}", exc_info=True)
        return False
