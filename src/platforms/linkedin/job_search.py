import time
import random
from playwright.sync_api import Page


def build_search_url(keyword: str, filters: dict) -> str:
    base = "https://www.linkedin.com/jobs/search/?"
    params = [f"keywords={keyword.replace(' ', '%20')}"]

    modality = filters.get("modality", [])
    if "remote" in modality:
        params.append("f_WT=2")
    elif "hybrid" in modality:
        params.append("f_WT=3")

    params.append("f_LF=f_AL")  # Easy Apply filter
    params.append("sortBy=DD")  # Más recientes primero

    return base + "&".join(params)


def extract_jobs_from_page(page: Page, limit: int = 25) -> list[dict]:
    jobs = []
    try:
        job_cards = page.query_selector_all(".job-card-container")[:limit]
        for card in job_cards:
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
            except Exception:
                continue
    except Exception as e:
        print(f"[LinkedIn] Error extrayendo jobs: {e}")
    return jobs


def get_job_description(page: Page, job: dict) -> str:
    try:
        page.goto(job["url"], timeout=30000)
        time.sleep(random.uniform(2, 4))
        desc_el = page.query_selector(".jobs-description__content")
        if desc_el:
            return desc_el.inner_text().strip()[:3000]
    except Exception as e:
        print(f"[LinkedIn] Error obteniendo descripción: {e}")
    return ""


def search_jobs(page: Page, filters: dict, limit: int = 50) -> list[dict]:
    all_jobs = []
    keywords = filters.get("search", {}).get("keywords", ["Software Engineer"])

    for keyword in keywords[:3]:  # Máximo 3 keywords por ejecución
        print(f"[LinkedIn] Buscando: {keyword}")
        url = build_search_url(keyword, filters.get("search", {}))
        try:
            page.goto(url, timeout=30000)
            time.sleep(random.uniform(3, 5))
            jobs = extract_jobs_from_page(page, limit=limit // len(keywords[:3]))
            all_jobs.extend(jobs)
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"[LinkedIn] Error buscando '{keyword}': {e}")

    # Eliminar duplicados por id
    seen = set()
    unique = []
    for job in all_jobs:
        if job["id"] not in seen:
            seen.add(job["id"])
            unique.append(job)

    print(f"[LinkedIn] {len(unique)} ofertas únicas encontradas")
    return unique
