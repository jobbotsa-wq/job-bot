import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger("jobbot")


def get_db_path(user_id: str) -> str:
    base = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"{user_id}.db")


def init_db(user_id: str) -> sqlite3.Connection:
    path = get_db_path(user_id)
    logger.debug(f"Abriendo base de datos: {path}")
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE,
            title TEXT,
            company TEXT,
            platform TEXT,
            url TEXT,
            match_score INTEGER,
            status TEXT,
            applied_at TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    logger.info(f"Base de datos lista para usuario '{user_id}'")
    return conn


def already_applied(conn: sqlite3.Connection, job_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM applications WHERE job_id = ?", (job_id,)
    ).fetchone()
    result = row is not None
    if result:
        logger.debug(f"Job ya aplicado anteriormente: {job_id}")
    return result


def save_application(conn: sqlite3.Connection, job: dict, status: str = "applied"):
    logger.debug(
        f"Guardando aplicacion | job_id={job.get('id')} | "
        f"titulo='{job.get('title')}' | empresa='{job.get('company')}' | "
        f"status={status} | score={job.get('match_score', 0)}"
    )
    conn.execute("""
        INSERT OR IGNORE INTO applications
        (job_id, title, company, platform, url, match_score, status, applied_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job.get("id"),
        job.get("title"),
        job.get("company"),
        job.get("platform"),
        job.get("url"),
        job.get("match_score", 0),
        status,
        datetime.now().isoformat(),
        job.get("notes", ""),
    ))
    conn.commit()
    logger.info(f"Guardado [{status}]: '{job.get('title')}' @ {job.get('company')}")


def get_applications(conn: sqlite3.Connection, limit: int = 100) -> list:
    rows = conn.execute(
        "SELECT * FROM applications ORDER BY applied_at DESC LIMIT ?", (limit,)
    ).fetchall()
    cols = ["id", "job_id", "title", "company", "platform", "url",
            "match_score", "status", "applied_at", "notes"]
    logger.debug(f"Recuperadas {len(rows)} aplicaciones de la BD")
    return [dict(zip(cols, row)) for row in rows]
