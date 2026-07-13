from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from . import db  # noqa: E402
from .config import COMPANIES, POLL_INTERVAL_MINUTES  # noqa: E402
from .poller import poll_all  # noqa: E402

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="Job Dashboard")
scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup():
    db.init_db()
    scheduler.add_job(poll_all, "interval", minutes=POLL_INTERVAL_MINUTES, next_run_time=None)
    scheduler.start()
    # kick off an immediate poll in the background
    import asyncio

    asyncio.create_task(poll_all())


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown(wait=False)


@app.get("/api/jobs")
def get_jobs(company: str | None = None, limit: int = 200):
    with db.get_conn() as conn:
        return db.list_jobs(conn, company=company, limit=limit)


@app.get("/api/companies")
def get_companies():
    return [{"name": c.name, "ats": c.ats} for c in COMPANIES]


@app.get("/api/health")
def get_health():
    with db.get_conn() as conn:
        return db.latest_poll_status(conn)


@app.get("/api/errors")
def get_errors(limit: int = 50):
    with db.get_conn() as conn:
        return db.recent_errors(conn, limit=limit)


@app.post("/api/poll")
async def trigger_poll():
    new_jobs = await poll_all()
    return {"new_jobs": len(new_jobs)}


class AppliedUpdate(BaseModel):
    id: str
    applied: bool


@app.post("/api/jobs/applied")
def set_applied(update: AppliedUpdate):
    applied_at = datetime.now(timezone.utc).isoformat() if update.applied else None
    with db.get_conn() as conn:
        updated = db.set_applied(conn, update.id, update.applied, applied_at)
    if not updated:
        raise HTTPException(status_code=404, detail="job not found")
    return {"id": update.id, "applied": update.applied, "applied_at": applied_at}


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")
