import time
import random
import logging
from playwright.sync_api import Page

logger = logging.getLogger("jobbot")


def build_search_url(keyword: str, filters: dict) -> str:
    base = "https://www.linkedin.com/jobs/search/?"
    params = [f"keywords={keyword.replace(' ', '%20')}"]

    modality = filters.get("modality", [])
    if "remote" in modality:
        params.append("f_WT=2")
        logger.debug("Filtro modalidad: remote (f_WT=2)")
    elif "hybrid" in modality:
        params.append("f_WT=3")
        logger.debug("Filtro modalidad: hybrid (f_WT=3)")

    params.append("f_LF=f_AL")
    params.append("sortBy=DD")

    url = base + "&".join(params)
    logger.debug(f"URL de busqueda construida: {url}")
    return url


def extract_jobs_from_page(page: Page, limit: int = 25) -> list[dict]:
    jobs = []
    logger.debug(f"Extrayendo hasta {limit} tarjetas de ofertas del DOM")
    try:
        job_cards = page.query_selector_all(".job-card-container")
        logger.debug(f"Tarjetas encontradas en pagina: {len(job_cards)} (limitando a {limit})")
        job_cards = job_cards[:limit]

        for i, card in enumerate(job_cards):
            try:
                job_id = card.get_attribute("data-job-id") or ""
                title_el = card.query_selector(".job-card-list__title")
                company_el = card.query_selector(".job-card-container__company-name")
                link_el = card.query_selector("a.job-card-container__link")

                title = title_el.inner_text().strip() if title_el else ""
                company = company_el.inner_text().strip() if company_el else ""
                url = "https://www.linkedin.com" + link_el.get_attribute("href") if link_el else ""

                if title and job_id:
                    jobs.append({
                        "id": f"linkedin_{job_id}",
                        "title": title,
                        "company": company,
                        "url": url,
                        "platform": "linkedin",
                        "description": "",
                    })
                    logger.debug(f"  Tarjeta {i+1}: '{title}' @ {company} (id={job_id})")
                else:
                    logger.warning(f"  Tarjeta {i+1}: sin titulo o job_id — omitida")
            except Exception as e:
                logger.warning(f"  Error leyendo tarjeta {i+1}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error extrayendo tarjetas de ofertas: {e}", exc_info=True)

    logger.debug(f"Extraidas {len(jobs)} ofertas validas de la pagina")
    return jobs


def get_job_description(page: Page, job: dict) -> str:
    title = job.get("title", "")
    logger.debug(f"Obteniendo descripcion de: '{title}' — URL: {job.get('url', '')[:60]}")
    try:
        page.goto(job["url"], timeout=30000)
        time.sleep(random.uniform(2, 4))
        desc_el = page.query_selector(".jobs-description__content")
        if desc_el:
            text = desc_el.inner_text().strip()[:3000]
            logger.debug(f"Descripcion obtenida: {len(text)} chars para '{title}'")
            return text
        else:
            logger.warning(f"No se encontro elemento de descripcion para '{title}'")
    except Exception as e:
        logger.error(f"Error obteniendo descripcion de '{title}': {e}", exc_info=True)
    return ""


def search_jobs(page: Page, filters: dict, limit: int = 50) -> list[dict]:
    all_jobs = []
    keywords = filters.get("search", {}).get("keywords", ["Software Engineer"])
    active_keywords = keywords[:3]
    logger.info(f"Iniciando busqueda en LinkedIn | keywords: {active_keywords} | limite: {limit}")

    for keyword in active_keywords:
        logger.info(f"Buscando keyword: '{keyword}'")
        url = build_search_url(keyword, filters.get("search", {}))
        try:
            page.goto(url, timeout=30000)
            time.sleep(random.uniform(3, 5))
            per_keyword = limit // len(active_keywords)
            jobs = extract_jobs_from_page(page, limit=per_keyword)
            logger.info(f"  '{keyword}': {len(jobs)} ofertas encontradas")
            all_jobs.extend(jobs)
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            logger.error(f"Error en busqueda de '{keyword}': {e}", exc_info=True)

    seen = set()
    unique = []
    for job in all_jobs:
        if job["id"] not in seen:
            seen.add(job["id"])
            unique.append(job)

    duplicates = len(all_jobs) - len(unique)
    logger.info(
        f"Busqueda completada | total: {len(all_jobs)} | "
        f"duplicados eliminados: {duplicates} | unicas: {len(unique)}"
    )
    return unique
