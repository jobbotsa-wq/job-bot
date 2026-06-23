import os
import yaml
import time
import random
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

from src.logger import setup_logger
from src.core.cv_parser import extract_cv_text
from src.core.job_matcher import setup_gemini, score_job
from src.platforms.linkedin import linkedin_login, search_jobs, apply_easy_apply
from src.platforms.linkedin.job_search import get_job_description
from src.storage.db import init_db, already_applied, save_application
from src.notifier.email_notifier import send_summary_email


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_credentials(creds_path: str) -> dict:
    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            f"Credenciales no encontradas: {creds_path}\n"
            f"Copia credentials.yaml.example como credentials.yaml y completalo."
        )
    return load_yaml(creds_path)


def run_for_user(user_dir: str, global_config: dict):
    user_id = os.path.basename(user_dir)
    logger = setup_logger(user_id)

    logger.info(f"{'='*60}")
    logger.info(f"INICIO DE EJECUCION — usuario: {user_id}")
    logger.info(f"Fecha/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Directorio usuario: {user_dir}")
    logger.info(f"{'='*60}")

    # Cargar configuracion
    profile_path = os.path.join(user_dir, "profile.yaml")
    creds_path = os.path.join(user_dir, "credentials.yaml")
    logger.debug(f"Cargando perfil: {profile_path}")
    profile = load_yaml(profile_path)
    logger.info(f"Perfil cargado: {profile.get('personal', {}).get('name', 'sin nombre')}")

    logger.debug(f"Cargando credenciales: {creds_path}")
    credentials = load_credentials(creds_path)
    logger.info("Credenciales cargadas correctamente")

    # CV
    cv_path = os.path.join(user_dir, profile.get("personal", {}).get("cv_path", "cv/cv.pdf"))
    logger.info(f"Ruta CV configurada: {cv_path}")
    cv_text = extract_cv_text(cv_path)
    if not cv_text:
        logger.warning("CV no disponible — el scoring sera menos preciso sin informacion del CV")

    # Gemini AI
    gemini_key = credentials.get("ai", {}).get("gemini_api_key", "")
    gemini_model = setup_gemini(gemini_key) if gemini_key else None
    if not gemini_model:
        logger.warning("Gemini no configurado — se aplicara a ofertas sin scoring de IA")

    min_score = (
        profile.get("filters", {}).get("min_match_score") or
        global_config.get("ai", {}).get("min_match_score", 70)
    )
    max_apps = (
        profile.get("filters", {}).get("max_applications_per_run") or
        global_config.get("platforms", {}).get("linkedin", {}).get("max_applications_per_run", 15)
    )
    logger.info(f"Configuracion: min_score={min_score} | max_aplicaciones={max_apps}")

    # Base de datos
    conn = init_db(user_id)

    results = {"applied": [], "skipped": [], "errors": []}
    applications_count = 0

    logger.info("Iniciando navegador Playwright (headless Chromium)")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        logger.debug("Navegador listo")

        # --- LinkedIn ---
        linkedin_enabled = profile.get("platforms", {}).get("linkedin", {}).get("enabled", True)
        logger.info(f"LinkedIn habilitado: {linkedin_enabled}")

        if linkedin_enabled:
            li_creds = credentials.get("linkedin", {})
            login_ok = linkedin_login(page, li_creds.get("email", ""), li_creds.get("password", ""))

            if not login_ok:
                msg = "LinkedIn: Login fallido — abortando plataforma"
                logger.error(msg)
                results["errors"].append(msg)
            else:
                logger.info("Iniciando busqueda de ofertas en LinkedIn")
                jobs = search_jobs(page, profile, limit=50)
                logger.info(f"Total ofertas a evaluar: {len(jobs)}")

                for idx, job in enumerate(jobs, 1):
                    logger.info(f"--- Oferta {idx}/{len(jobs)}: '{job['title']}' @ {job['company']} ---")

                    if applications_count >= max_apps:
                        logger.info(f"Limite de {max_apps} aplicaciones alcanzado — deteniendo")
                        break

                    if already_applied(conn, job["id"]):
                        logger.info(f"Omitida (ya aplicada): '{job['title']}'")
                        continue

                    # Obtener descripcion completa
                    logger.debug("Obteniendo descripcion completa de la oferta")
                    job["description"] = get_job_description(page, job)

                    # Scoring con Gemini
                    if gemini_model:
                        match = score_job(gemini_model, profile, cv_text, job)
                        job["match_score"] = match.get("score", 0)
                        job["notes"] = match.get("reason", "")

                        if not match.get("apply") or job["match_score"] < min_score:
                            logger.info(
                                f"Omitida por score bajo ({job['match_score']}/{min_score}): "
                                f"'{job['title']}' — {job['notes'][:80]}"
                            )
                            save_application(conn, job, status="skipped_score")
                            continue
                    else:
                        job["match_score"] = 75
                        job["notes"] = "Sin scoring IA"
                        logger.debug("Scoring omitido (Gemini no configurado) — score por defecto 75")

                    # Aplicar
                    logger.info(f"Aplicando (score={job['match_score']}): '{job['title']}' @ {job['company']}")
                    apply_result = apply_easy_apply(page, job, profile)
                    job["notes"] += f" | {apply_result.get('notes', '')}"

                    if apply_result["status"] == "applied":
                        save_application(conn, job, status="applied")
                        results["applied"].append(job)
                        applications_count += 1
                        logger.info(f"EXITO: aplicacion #{applications_count} enviada")
                    elif apply_result["status"] == "skipped":
                        save_application(conn, job, status="skipped_external")
                        results["skipped"].append(job)
                        logger.info(f"Omitida (link externo): '{job['title']}'")
                    else:
                        save_application(conn, job, status="error")
                        error_msg = f"{job['title']}: {apply_result.get('notes', '')}"
                        results["errors"].append(error_msg)
                        logger.error(f"Error en aplicacion: {error_msg}")

                    delay = random.uniform(10, 20)
                    logger.debug(f"Esperando {delay:.1f}s antes de la siguiente oferta")
                    time.sleep(delay)

        logger.info("Cerrando navegador")
        browser.close()

    # Email de resumen
    gmail_cfg = credentials.get("gmail", {})
    to_email = profile.get("personal", {}).get("email_notifications", "")
    user_name = profile.get("personal", {}).get("name", user_id)

    if gmail_cfg and to_email:
        send_summary_email(gmail_cfg, user_name, to_email, results)
    else:
        logger.warning("Email de resumen no enviado — gmail o email_notifications no configurados")

    logger.info(f"{'='*60}")
    logger.info(
        f"FIN EJECUCION {user_id} | "
        f"aplicadas={len(results['applied'])} | "
        f"externas={len(results['skipped'])} | "
        f"errores={len(results['errors'])}"
    )
    logger.info(f"{'='*60}")
    return results


def run_all_users():
    base = Path(__file__).parent.parent.parent
    config = load_yaml(str(base / "config" / "settings.yaml"))
    users_dir = base / "users"

    logger = setup_logger("main")
    logger.info(f"Job Bot iniciado | usuarios en: {users_dir}")

    user_dirs = [d for d in sorted(users_dir.iterdir()) if d.is_dir()]
    logger.info(f"Usuarios encontrados: {[d.name for d in user_dirs]}")

    for user_dir in user_dirs:
        try:
            run_for_user(str(user_dir), config)
        except FileNotFoundError as e:
            logging_fallback = setup_logger("main")
            logging_fallback.error(f"Usuario {user_dir.name}: {e}")
        except Exception as e:
            logging_fallback = setup_logger("main")
            logging_fallback.error(
                f"Error inesperado procesando {user_dir.name}: {e}", exc_info=True
            )
