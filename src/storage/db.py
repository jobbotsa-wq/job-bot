import sqlite3
import os
from datetime import datetime


def get_db_path(user_id: str) -> str:
    base = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"{user_id}.db")


def init_db(user_id: str) -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(user_id))
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
    return conn


def already_applied(conn: sqlite3.Connection, job_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM applications WHERE job_id = ?", (job_id,)
    ).fetchone()
    return row is not None


def save_application(conn: sqlite3.Connection, job: dict, status: str = "applied"):
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


def get_applications(conn: sqlite3.Connection, limit: int = 100) -> list:
    rows = conn.execute(
        "SELECT * FROM applications ORDER BY applied_at DESC LIMIT ?", (limit,)
    ).fetchall()
    cols = ["id", "job_id", "title", "company", "platform", "url",
            "match_score", "status", "applied_at", "notes"]
    return [dict(zip(cols, row)) for row in rows]
