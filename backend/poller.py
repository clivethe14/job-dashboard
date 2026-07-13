import asyncio
import logging
from datetime import datetime, timezone

import httpx

from . import db
from .adapters import ashby, custom, eightfold, github_newgrad, greenhouse, lever, smartrecruiters, workday
from .adapters.base import Company, matches_keywords
from .config import COMPANIES
from .logging_setup import setup_logging
from .notifier import notify_new_jobs

setup_logging()
log = logging.getLogger("poller")

FETCHERS = {
    "greenhouse": greenhouse.fetch,
    "lever": lever.fetch,
    "workday": workday.fetch,
    "ashby": ashby.fetch,
    "smartrecruiters": smartrecruiters.fetch,
    "eightfold": eightfold.fetch,
    "github_newgrad": github_newgrad.fetch,
}


def _resolve_fetcher(company: Company):
    if company.ats == "custom":
        fn_name = company.extra.get("fn")
        return getattr(custom, fn_name, None) if fn_name else None
    return FETCHERS.get(company.ats)


async def poll_company(client: httpx.AsyncClient, company: Company) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    fetcher = _resolve_fetcher(company)
    if fetcher is None:
        with db.get_conn() as conn:
            db.log_poll(conn, company.name, now, "error", error=f"no fetcher registered for ats={company.ats!r}")
        log.warning("%s: no fetcher registered for ats=%r", company.name, company.ats)
        return []
    try:
        jobs = await fetcher(client, company)
        jobs = [j for j in jobs if matches_keywords(j["title"], company.keywords)]
        new_jobs = []
        with db.get_conn() as conn:
            for j in jobs:
                if not db.job_exists(conn, j["id"]):
                    db.insert_job(conn, j, first_seen_at=now)
                    new_jobs.append(j)
            db.log_poll(conn, company.name, now, "ok", new_jobs=len(new_jobs))
        if new_jobs:
            log.info("%s: %d new job(s)", company.name, len(new_jobs))
        return new_jobs
    except Exception as e:  # noqa: BLE001
        log.warning("%s: poll failed: %s", company.name, e)
        with db.get_conn() as conn:
            db.log_poll(conn, company.name, now, "error", error=str(e))
        return []


EMAIL_LABEL = "Email alerts"


def _notify_and_log(new_jobs: list[dict]) -> None:
    """Send the alert email and record the outcome in poll_log so the dashboard's
    debug sidebar surfaces SMTP failures alongside per-company poll errors."""
    if not new_jobs:
        return
    now = datetime.now(timezone.utc).isoformat()
    try:
        sent = notify_new_jobs(new_jobs)
        if sent:
            with db.get_conn() as conn:
                db.log_poll(conn, EMAIL_LABEL, now, "ok", new_jobs=len(new_jobs))
            log.info("email alert sent for %d job(s)", len(new_jobs))
    except Exception as e:  # noqa: BLE001
        log.warning("email send failed: %s", e)
        with db.get_conn() as conn:
            db.log_poll(conn, EMAIL_LABEL, now, "error", error=str(e))


async def poll_all() -> list[dict]:
    all_new = []
    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0 (job-dashboard local poller)"}) as client:
        results = await asyncio.gather(*[poll_company(client, c) for c in COMPANIES])
    for r in results:
        all_new.extend(r)
    _notify_and_log(all_new)
    return all_new


def run_poll_sync():
    return asyncio.run(poll_all())
