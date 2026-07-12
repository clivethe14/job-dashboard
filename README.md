# Job Dashboard

Local web dashboard that polls target companies' career-page APIs on a schedule and surfaces new software-engineering postings as soon as they appear, with email alerts.

## Setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # then fill in SMTP credentials
```

## Run

```
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000

## Configuration

- `backend/config.py` — list of companies, their ATS type, and poll interval (default: 60 min).
- `.env` — SMTP credentials for email alerts (Gmail App Password recommended).
- `data/jobs.db` — SQLite database of seen postings (auto-created).
- `logs/dashboard.log` — app log, created on first run. Useful if the whole process fails to start (the in-app Debug sidebar only tracks per-company poll errors, not startup crashes).

## Auto-start at logon

Run `.\setup_startup_shortcut.ps1` once — it drops a shortcut to `start_dashboard.bat` in your Startup folder, so the dashboard launches silently (no console window, via `pythonw.exe`) every time you log in. This is the recommended method; `setup_scheduled_task.ps1` (Task Scheduler) is kept as an alternative but may be blocked by Group Policy on managed machines.

To start it immediately without logging off: double-click `start_dashboard.bat`, or run `Start-Process "start_dashboard.bat"` from PowerShell.

## Adding a company

Add a `Company(name=..., ats=..., token=...)` entry to `COMPANIES` in `backend/config.py`.
Supported `ats` values: `greenhouse`, `lever`, `workday` (needs `extra={"tenant":..., "site":...}`), or a custom function registered in `backend/adapters/custom.py`.
