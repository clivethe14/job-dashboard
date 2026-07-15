"""Application-documents folder management.

One folder per job application: <APPLICATIONS_DIR>\\<Company>\\<Job Title>\\.
Created when the user first Views a job (or uploads documents), populated when
they mark it Applied, moved to the Recycle Bin when they mark it Not a fit.

All path construction and deletion safety lives here: nothing outside
APPLICATIONS_DIR is ever created or deleted, non-empty company folders are
never removed, and folders of applied jobs are never deleted.
"""

import os
import re
from pathlib import Path

from send2trash import send2trash

DEFAULT_DIR = r"D:\Documents\Job Applications"

_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def applications_dir() -> Path:
    base = Path(os.environ.get("APPLICATIONS_DIR", DEFAULT_DIR))
    base.mkdir(parents=True, exist_ok=True)
    return base


def sanitize_component(name: str, max_len: int = 80) -> str:
    s = re.sub(r'[\\/:*?"<>|]', " ", name or "")
    s = re.sub(r"\s+", " ", s).strip().strip(". ")
    if not s:
        s = "Untitled"
    if s.upper() in _RESERVED:
        s = f"{s}_"
    return s[:max_len].rstrip(". ")


def _short_suffix(job_id: str) -> str:
    tail = re.sub(r"[^A-Za-z0-9]", "", job_id)[-4:] or "x"
    return f" ({tail})"


def ensure_folder(conn, job: dict) -> str:
    """Create (idempotently) the job's folder and persist folder_path on the row.
    Returns the absolute path as a string."""
    from . import db

    existing = job.get("folder_path")
    if existing:
        p = Path(existing)
        p.mkdir(parents=True, exist_ok=True)
        return str(p)

    base = applications_dir()
    company_dir = base / sanitize_component(job["company"])
    title_name = sanitize_component(job["title"])
    folder = company_dir / title_name

    # collision: same sanitized path already claimed by a DIFFERENT job id
    row = conn.execute(
        "SELECT id FROM jobs WHERE folder_path = ? AND id != ?",
        (str(folder), job["id"]),
    ).fetchone()
    if row is not None:
        folder = company_dir / (title_name[: 80 - 7] + _short_suffix(job["id"]))

    folder.mkdir(parents=True, exist_ok=True)
    db.set_folder_path(conn, job["id"], str(folder))
    return str(folder)


def _is_inside_applications_dir(path: Path) -> bool:
    try:
        path.resolve().relative_to(applications_dir().resolve())
        return True
    except ValueError:
        return False


def delete_folder(conn, job: dict) -> bool:
    """Move the job's folder to the Recycle Bin. Returns True if deleted.
    Refuses when: no folder recorded, folder missing, job applied, or the path
    escapes APPLICATIONS_DIR."""
    from . import db

    if job.get("applied"):
        return False
    folder_path = job.get("folder_path")
    if not folder_path:
        return False
    folder = Path(folder_path)
    if not folder.is_dir() or not _is_inside_applications_dir(folder):
        # stale/foreign path: clear the record but touch nothing on disk
        db.set_folder_path(conn, job["id"], None)
        return False

    send2trash(str(folder))
    db.set_folder_path(conn, job["id"], None)

    company_dir = folder.parent
    if (
        company_dir != applications_dir()
        and _is_inside_applications_dir(company_dir)
        and company_dir.is_dir()
        and not any(company_dir.iterdir())
    ):
        company_dir.rmdir()
    return True


def save_documents(folder_path: str, files: list[tuple[str, bytes]]) -> list[str]:
    """Write (filename, content) pairs into the folder, deduping names with
    ' (1)', ' (2)' suffixes. Returns the saved filenames."""
    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)
    saved = []
    for raw_name, content in files:
        name = sanitize_component(Path(raw_name).stem, max_len=100)
        ext = re.sub(r'[\\/:*?"<>|]', "", Path(raw_name).suffix)[:10]
        candidate = folder / f"{name}{ext}"
        counter = 1
        while candidate.exists():
            candidate = folder / f"{name} ({counter}){ext}"
            counter += 1
        candidate.write_bytes(content)
        saved.append(candidate.name)
    return saved


def list_documents(folder_path: str | None) -> list[str]:
    if not folder_path:
        return []
    folder = Path(folder_path)
    if not folder.is_dir():
        return []
    return sorted(f.name for f in folder.iterdir() if f.is_file())


def open_folder(folder_path: str) -> None:
    os.startfile(folder_path)  # noqa: S606 — local single-user app
