import time
import random
from playwright.sync_api import Page


def linkedin_login(page: Page, email: str, password: str) -> bool:
    try:
        page.goto("https://www.linkedin.com/login", timeout=30000)
        time.sleep(random.uniform(2, 4))

        page.fill("#username", email)
        time.sleep(random.uniform(0.5, 1.5))
        page.fill("#password", password)
        time.sleep(random.uniform(0.5, 1.5))
        page.click('[type="submit"]')
        time.sleep(random.uniform(3, 5))

        # Verificar login exitoso
        if "feed" in page.url or "mynetwork" in page.url:
            print("[LinkedIn] Login exitoso")
            return True

        # Detectar captcha o verificación
        if "checkpoint" in page.url or "challenge" in page.url:
            print("[LinkedIn] Se requiere verificación manual. Revisar cuenta.")
            return False

        print(f"[LinkedIn] Login falló. URL actual: {page.url}")
        return False

    except Exception as e:
        print(f"[LinkedIn] Error en login: {e}")
        return False
