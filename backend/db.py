import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT,
    url TEXT NOT NULL,
    posted_at TEXT,
    first_seen_at TEXT NOT NULL,
    notified INTEGER NOT NULL DEFAULT 0,
    applied INTEGER NOT NULL DEFAULT 0,
    applied_at TEXT,
    source TEXT NOT NULL DEFAULT 'ats',
    sponsorship TEXT,
    dismissed INTEGER NOT NULL DEFAULT 0,
    dismissed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_first_seen ON jobs(first_seen_at);

CREATE TABLE IF NOT EXISTS poll_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    ran_at TEXT NOT NULL,
    status TEXT NOT NULL,
    new_jobs INTEGER NOT NULL DEFAULT 0,
    error TEXT
);
"""


@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _migrate(conn):
    """Add columns introduced after the DB was first created. CREATE TABLE IF NOT
    EXISTS in SCHEMA only applies to fresh databases, so existing ones need this."""
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(jobs)").fetchall()}
    if "applied" not in cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN applied INTEGER NOT NULL DEFAULT 0")
    if "applied_at" not in cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN applied_at TEXT")
    if "source" not in cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN source TEXT NOT NULL DEFAULT 'ats'")
    if "sponsorship" not in cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN sponsorship TEXT")
    if "dismissed" not in cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN dismissed INTEGER NOT NULL DEFAULT 0")
    if "dismissed_at" not in cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN dismissed_at TEXT")


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)


def job_exists(conn, job_id: str) -> bool:
    row = conn.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return row is not None


def insert_job(conn, job: dict, first_seen_at: str):
    conn.execute(
        """INSERT OR IGNORE INTO jobs (id, company, title, location, url, posted_at, first_seen_at, source, sponsorship)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            job["id"],
            job["company"],
            job["title"],
            job.get("location"),
            job["url"],
            job.get("posted_at"),
            first_seen_at,
            job.get("source", "ats"),
            job.get("sponsorship"),
        ),
    )


def log_poll(conn, company: str, ran_at: str, status: str, new_jobs: int = 0, error: str | None = None):
    conn.execute(
        "INSERT INTO poll_log (company, ran_at, status, new_jobs, error) VALUES (?, ?, ?, ?, ?)",
        (company, ran_at, status, new_jobs, error),
    )


def list_jobs(conn, company: str | None = None, limit: int = 200):
    query = "SELECT * FROM jobs"
    params = []
    if company:
        query += " WHERE company = ?"
        params.append(company)
    query += " ORDER BY first_seen_at DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in conn.execute(query, params).fetchall()]


def unnotified_jobs(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM jobs WHERE notified = 0").fetchall()]


def mark_notified(conn, job_ids: list[str]):
    conn.executemany("UPDATE jobs SET notified = 1 WHERE id = ?", [(jid,) for jid in job_ids])


def set_applied(conn, job_id: str, applied: bool, applied_at: str | None) -> bool:
    """Returns True if a row was updated, False if job_id doesn't exist."""
    cur = conn.execute(
        "UPDATE jobs SET applied = ?, applied_at = ? WHERE id = ?",
        (1 if applied else 0, applied_at if applied else None, job_id),
    )
    return cur.rowcount > 0


def set_dismissed(conn, job_id: str, dismissed: bool, dismissed_at: str | None) -> bool:
    """Returns True if a row was updated, False if job_id doesn't exist."""
    cur = conn.execute(
        "UPDATE jobs SET dismissed = ?, dismissed_at = ? WHERE id = ?",
        (1 if dismissed else 0, dismissed_at if dismissed else None, job_id),
    )
    return cur.rowcount > 0


def latest_poll_status(conn):
    """Most recent poll_log row per company, newest first by ran_at."""
    rows = conn.execute(
        """SELECT p1.company, p1.status, p1.ran_at, p1.new_jobs, p1.error
           FROM poll_log p1
           WHERE p1.id = (SELECT MAX(p2.id) FROM poll_log p2 WHERE p2.company = p1.company)
           ORDER BY p1.company"""
    ).fetchall()
    return [dict(r) for r in rows]


def recent_errors(conn, limit: int = 50):
    rows = conn.execute(
        "SELECT company, ran_at, error FROM poll_log WHERE status = 'error' ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
