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
Supported `ats` values: `greenhouse`, `lever`, `workday` (needs `extra={"tenant":..., "site":...}`), `ashby`, `smartrecruiters`, `eightfold`, `github_newgrad`, or a custom function registered in `backend/adapters/custom.py`.

## Sources beyond standard ATS platforms

- **Microsoft / Apple / Google** — direct custom adapters (`backend/adapters/custom.py`). These parse each site's own (unofficial) data format, so they are more brittle than ATS APIs; they fail loudly into `poll_log`, so any breakage shows in the Debug sidebar.
- **New-Grad Feed (GitHub)** — ingests the community-maintained [SimplifyJobs/New-Grad-Positions](https://github.com/SimplifyJobs/New-Grad-Positions) `listings.json`. Covers ~900 companies' early-career US roles (incl. companies with unscrapeable sites), each with a sponsorship flag surfaced as a badge. These listings keep their real company name but won't appear in the company-filter dropdown (which is built from the config list).

### Known-hard sources (not integrated; use native email alerts on their sites)

- **Meta** — GraphQL is bot-blocked to plain HTTP clients; the DirectEmployers mirror only refreshes ~weekly. Covered by the GitHub feed + native alerts.
- **IBM** — `www-api.ibm.com/search/api/v2` is live but needs its exact request payload captured from the careers site's network traffic.
- **Oracle** — Oracle Recruiting Cloud REST works but needs the real `siteNumber` for Oracle's own tenant (capture from careers.oracle.com).
- **Bloomberg / Two Sigma / Atlassian** (Avature), **Citadel** (bot-blocked), **SAP** (SuccessFactors, auth-gated) — no clean public feed.
