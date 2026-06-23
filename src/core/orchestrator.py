import os
import yaml
import time
import random
from pathlib import Path
from playwright.sync_api import sync_playwright

from src.core.cv_parser import extract_cv_text
from src.core.job_matcher import setup_gemini, score_job
from src.platforms.linkedin import linkedin_login, search_jobs, apply_easy_apply
from src.storage.db import init_db, already_applied, save_application
from src.notifier.email_notifier import send_summary_email


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_credentials(creds_path: str) -> dict:
    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            f"Archivo de credenciales no encontrado: {creds_path}\n"
            f"Copia credentials.yaml.example como credentials.yaml y complétalo."
        )
    return load_yaml(creds_path)


def run_for_user(user_dir: str, global_config: dict):
    user_id = os.path.basename(user_dir)
    print(f"\n{'='*50}")
    print(f"[Bot] Procesando usuario: {user_id}")
    print(f"{'='*50}")

    profile = load_yaml(os.path.join(user_dir, "profile.yaml"))
    credentials = load_credentials(os.path.join(user_dir, "credentials.yaml"))

    # CV
    cv_path = os.path.join(user_dir, profile.get("personal", {}).get("cv_path", "cv.pdf"))
    cv_text = extract_cv_text(cv_path)
    if cv_text:
        print(f"[CV] Extraídos {len(cv_text)} caracteres del CV")
    else:
        print("[CV] No se pudo leer el CV, continuando sin él")

    # Gemini AI
    gemini_key = credentials.get("ai", {}).get("gemini_api_key", "")
    gemini_model = setup_gemini(gemini_key) if gemini_key else None
    min_score = profile.get("filters", {}).get("min_match_score") or \
                global_config.get("ai", {}).get("min_match_score", 70)
    max_apps = profile.get("filters", {}).get("max_applications_per_run") or \
               global_config.get("platforms", {}).get("linkedin", {}).get("max_applications_per_run", 15)

    # DB
    conn = init_db(user_id)

    results = {"applied": [], "skipped": [], "errors": []}
    applications_count = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        # LinkedIn
        if profile.get("platforms", {}).get("linkedin", {}).get("enabled", True):
            li_creds = credentials.get("linkedin", {})
            if not linkedin_login(page, li_creds.get("email", ""), li_creds.get("password", "")):
                results["errors"].append("LinkedIn: Error de login")
            else:
                jobs = search_jobs(page, profile, limit=50)

                for job in jobs:
                    if applications_count >= max_apps:
                        print(f"[Bot] Límite de {max_apps} aplicaciones alcanzado")
                        break

                    if already_applied(conn, job["id"]):
                        continue

                    # Enriquecer con descripción
                    from src.platforms.linkedin.job_search import get_job_description
                    job["description"] = get_job_description(page, job)

                    # Scoring con Gemini
                    if gemini_model:
                        match = score_job(gemini_model, profile, cv_text, job)
                        job["match_score"] = match.get("score", 0)
                        job["notes"] = match.get("reason", "")
                        if not match.get("apply") or job["match_score"] < min_score:
                            print(f"[Bot] Omitido (score {job['match_score']}): {job['title']}")
                            save_application(conn, job, status="skipped_score")
                            continue
                    else:
                        job["match_score"] = 75
                        job["notes"] = "Sin scoring de IA"

                    print(f"[Bot] Aplicando (score {job['match_score']}): {job['title']} @ {job['company']}")
                    apply_result = apply_easy_apply(page, job, profile)
                    job["notes"] += f" | {apply_result.get('notes', '')}"

                    if apply_result["status"] == "applied":
                        save_application(conn, job, status="applied")
                        results["applied"].append(job)
                        applications_count += 1
                    elif apply_result["status"] == "skipped":
                        save_application(conn, job, status="skipped_external")
                        results["skipped"].append(job)
                    else:
                        save_application(conn, job, status="error")
                        results["errors"].append(f"{job['title']}: {apply_result.get('notes')}")

                    delay = random.uniform(10, 20)
                    time.sleep(delay)

        browser.close()

    # Email de resumen
    gmail_cfg = credentials.get("gmail", {})
    to_email = profile.get("personal", {}).get("email_notifications", "")
    user_name = profile.get("personal", {}).get("name", user_id)

    if gmail_cfg and to_email:
        send_summary_email(gmail_cfg, user_name, to_email, results)

    print(f"\n[Bot] {user_id}: {len(results['applied'])} aplicadas, "
          f"{len(results['skipped'])} omitidas, {len(results['errors'])} errores")
    return results


def run_all_users():
    base = Path(__file__).parent.parent.parent
    config = load_yaml(str(base / "config" / "settings.yaml"))
    users_dir = base / "users"

    for user_dir in sorted(users_dir.iterdir()):
        if user_dir.is_dir():
            try:
                run_for_user(str(user_dir), config)
            except FileNotFoundError as e:
                print(f"[Bot] {e}")
            except Exception as e:
                print(f"[Bot] Error procesando {user_dir.name}: {e}")
