# Job Dashboard

A self-hosted job-posting tracker that watches the career sites of ~39 visa-sponsoring tech companies and tells you about new software-engineering roles **within the hour they're posted** — not days later through a job board.

It runs entirely on your own laptop. No subscriptions, no third-party service, no data leaving your machine except the requests it makes to each company's public careers API.

---

## Why this exists

If you're applying to competitive roles (especially on a visa timeline, where you want to be early), the single biggest controllable advantage is **applying within the first 24 hours of a posting going live**. Recruiters review in the order applications arrive, and popular reqs often close after a few hundred applicants.

Job boards aggregate slowly and inconsistently. This tool goes straight to the source: the same APIs each company's own careers page uses.

---

## What it does

- **Polls ~39 sources every hour** — Greenhouse, Lever, Workday, Ashby, SmartRecruiters, Eightfold boards, plus custom adapters for Amazon, Microsoft, Apple, Google and Uber, plus a community feed covering ~900 more companies.
- **Filters to roles you'd actually apply to** — entry/mid-level software, AI/ML, mobile, data and DevOps titles. Senior/Staff/Principal, management, internships and recruiter postings are excluded.
- **Emails you when new roles appear** — one batched email per poll, only for genuinely new postings. No new jobs, no email.
- **Tracks your pipeline** — mark jobs *Applied* or *Not a fit*; dismissed roles disappear from the list permanently.
- **Files your documents automatically** — creates a `Company\Job Title\` folder per application and stores the tailored resume/cover letter you used.
- **Shows when something breaks** — a Debug sidebar reports the health of every source, so a silently-dead scraper is visible instead of quietly returning nothing.

---

## Screens & concepts

| Concept | What it means |
|---|---|
| **NEW badge** | Posting first seen in the last 24 hours |
| **USA only** | Hides clearly non-US roles; keeps US and ambiguous ones ("Remote", bare city names) |
| **SPONSORS / NO SPONSORSHIP / US CITIZEN ONLY** | Sponsorship flags from the community feed — useful if you need visa sponsorship |
| **Hide applied / Show dismissed** | Keeps your review queue to just the undecided roles |
| **Debug sidebar** | Green/red health dot per source, plus recent errors (including email send failures) |

---

## Requirements

- **Windows 10/11** (the launcher scripts and Recycle-Bin integration are Windows-specific; the Python backend itself is cross-platform)
- **Python 3.12** ([python.org/downloads](https://www.python.org/downloads/)) — during install, tick **"Add Python to PATH"**
- **Git** (only if you're cloning rather than downloading a ZIP)
- A **Gmail account** for sending alerts (any SMTP provider works, but Gmail is free and the instructions below assume it)

---

## Step-by-step setup

### 1. Get the code

```powershell
git clone https://github.com/clivethe14/job-dashboard.git
cd job-dashboard
```

> **Note on paths:** all five helper scripts — `start_server.ps1`, `start_dashboard.bat`, `start_dashboard_silent.bat`, `setup_startup_shortcut.ps1` and `setup_scheduled_task.ps1` — contain the hard-coded path `D:\Documents\Claude\Job Dashbaord`. If you put the project anywhere else, open those files and replace that path with your own folder. The Python code itself is path-independent, so nothing under `backend/` needs changing.

### 2. Create the virtual environment and install dependencies

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

This installs FastAPI, APScheduler, httpx, and `curl_cffi` (needed because Uber's servers reject ordinary Python HTTPS requests — see *Known quirks* below).

### 3. Set up your email alerts

Alerts are sent **from** a Gmail account you control, **to** whatever address you choose. Google won't let apps sign in with your normal password, so you generate a free 16-character **App Password**.

**3a. Turn on 2-Step Verification** (required before App Passwords exist)

1. Go to <https://myaccount.google.com/security>
2. Under *How you sign in to Google*, enable **2-Step Verification**

**3b. Create the App Password**

1. Go to <https://myaccount.google.com/apppasswords>
2. Name it anything (e.g. `Job Dashboard`) → **Create**
3. Copy the 16-character code shown (e.g. `abcd efgh ijkl mnop`)

> If the App Passwords page says the option isn't available, 2-Step Verification isn't fully enabled yet — finish step 3a first.

**3c. Create your `.env` file**

```powershell
copy .env.example .env
```

Open `.env` in Notepad and fill it in:

```ini
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_sending_account@gmail.com
SMTP_PASSWORD=abcdefghijklmnop

# Who receives the alerts (comma-separated for multiple addresses)
MAIL_TO=where_you_want_alerts@gmail.com

# Optional: where application document folders are created
# Defaults to D:\Documents\Job Applications
#APPLICATIONS_DIR=D:\Documents\Job Applications
```

Notes:
- Spaces in the App Password are fine — they're stripped automatically.
- The sending account and the recipient **do not have to be the same address**.
- **Set `MAIL_TO`.** If you leave it out, the app falls back to a list of default addresses hard-coded in `backend/notifier.py`, which are the original author's — not yours.
- `.env` is gitignored, so your password is never committed.

### 4. Start the dashboard

**Option A — visible window (simplest, best while setting up):**

```powershell
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

That window **is** the server. Closing it or pressing `Ctrl+C` stops the dashboard.

**Option B — hidden in the background:**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\start_server.ps1"
```

No window, logs go to `logs\`. Stop it by ending `pythonw.exe` in Task Manager.

### 5. Open it

<http://127.0.0.1:8000>

The first poll runs immediately on startup and takes roughly 30–60 seconds to work through every source. Expect a few thousand postings on the first run — that initial batch will generate one large email, which is normal. After that you'll only hear about genuinely new roles.

### 6. (Optional) Start automatically at login

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_startup_shortcut.ps1
```

This drops a shortcut to `start_dashboard_silent.bat` in your Startup folder so the server launches quietly each time you log in. `setup_scheduled_task.ps1` does the same via Task Scheduler, but may be blocked by Group Policy on managed machines.

---

## Configuration

| File | What you can change |
|---|---|
| `backend/config.py` | The company list and `POLL_INTERVAL_MINUTES` (default `60`) |
| `backend/adapters/base.py` | `INCLUDE_KEYWORDS` / `EXCLUDE_KEYWORDS` — which job titles qualify |
| `.env` | SMTP credentials, `MAIL_TO`, `APPLICATIONS_DIR` |

**Changing which roles you see** — edit the two keyword lists in `backend/adapters/base.py`:

- `INCLUDE_KEYWORDS` — a title must contain at least one of these (substring match, lowercase)
- `EXCLUDE_KEYWORDS` — a title containing any of these is dropped (whole-word match, so `intern` won't wrongly hit "International")

Restart the server after editing either file.

**Adding a company** — add a `Company(...)` entry to `COMPANIES` in `backend/config.py`. Supported `ats` values: `greenhouse`, `lever`, `ashby`, `smartrecruiters`, `eightfold`, `workday` (needs `extra={"tenant":..., "site":..., "host":...}`), `github_newgrad`, or `custom` with `extra={"fn": "..."}` pointing at a function in `backend/adapters/custom.py`.

---

## How it works

```
                 ┌─────────────────────────────────────────────┐
  hourly  ──────▶│  poller.py  →  adapters/*  →  each careers   │
  scheduler      │                               API / site     │
                 └───────────────────┬─────────────────────────┘
                                     │ normalized postings
                                     ▼
                     title filter (INCLUDE / EXCLUDE keywords)
                                     │
                                     ▼
                   SQLite (data/jobs.db) — dedupes by job ID
                                     │
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
            email alert (new only)         dashboard at :8000
```

Deduplication is keyed on a stable `Company:JobID`, so re-polling never re-notifies you about a posting you've already seen, and your *Applied* / *Not a fit* marks survive every future poll.

**Data locations**

| Path | Contents | In git? |
|---|---|---|
| `data/jobs.db` | All seen postings + your applied/dismissed marks | No |
| `logs/dashboard.log` | Application log — check here if the server won't start | No |
| `.env` | Your SMTP credentials | No |
| `APPLICATIONS_DIR` | Per-application document folders | No |

---

## Job sources

**Standard ATS platforms (most reliable)** — Greenhouse (18): Stripe, Airbnb, Robinhood, Reddit, Figma, Coinbase, Pinterest, DoorDash, Databricks, Roblox, Twilio, Cloudflare, Asana, MongoDB, Elastic, Datadog, Lyft, Jane Street · Workday (8): Zoom, Nvidia, Salesforce, Adobe, Cisco, Capital One, VMware (Broadcom), Workday · Lever (2): Palantir, Spotify · Ashby (2): Notion, Snowflake · SmartRecruiters (2): Block, ServiceNow · Eightfold (1): Netflix

**Custom adapters (more fragile)** — Amazon, Microsoft, Apple, Google, Uber. These parse each site's own undocumented data format, so they break when a company redesigns its careers site. They fail loudly into the Debug sidebar rather than silently returning nothing.

**Community feed** — [SimplifyJobs/New-Grad-Positions](https://github.com/SimplifyJobs/New-Grad-Positions), ~1,100 early-career US roles across ~900 companies, each carrying a sponsorship flag. This covers many employers whose own sites can't be scraped. These postings keep their real company name but don't appear in the company-filter dropdown (which is built from the config list).

**Deliberately not integrated** — Meta (GraphQL is bot-blocked; its public mirror only refreshes weekly), IBM and Oracle (live endpoints, but each needs its exact request payload captured from browser traffic), and Bloomberg / Two Sigma / Atlassian / Citadel / SAP (no clean public feed). For these, set up native job alerts on their own career sites.

---

## Known quirks

**Polling only runs while the laptop is awake.** The scheduler lives inside the server process, so sleep, hibernate and shutdown all pause it. If the machine sleeps overnight, the next poll fires when you wake it — not on the hour you missed. To poll unattended, keep the laptop plugged in with sleep disabled, or host the app somewhere always-on.

**`pythonw.exe` must have its output redirected.** Launching the server with `pythonw` and no output redirection makes it die instantly and silently: it has no console, so the first log line it writes fails and kills the process. `start_server.ps1` handles this correctly. If you write your own launcher, either use `python.exe` (visible window) or redirect both stdout and stderr to files.

**Uber needs `curl_cffi`.** Uber's edge fingerprints the TLS handshake and returns `403` to Python's standard HTTPS stack regardless of headers. `curl_cffi` replays a real Chrome handshake, so the Uber adapter uses its own session instead of the shared HTTP client.

**Custom adapters will break eventually.** Amazon, Microsoft, Apple, Google and Uber all depend on undocumented internals. When a company rebuilds its careers site, that adapter starts erroring — visible as a red row in the Debug sidebar. Fixing it means finding the site's new data endpoint (browser DevTools → Network tab) and updating the adapter.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Browser can't reach `127.0.0.1:8000` | The server isn't running. Start it (step 4). Confirm with `netstat -ano \| findstr :8000` |
| Server window closes instantly | Something failed during startup — check `logs\dashboard.log` |
| No emails arriving | Check the Debug sidebar for an "Email alerts" error row. Verify `SMTP_USER` / `SMTP_PASSWORD` in `.env`, and check your Spam folder for the first one |
| Emails go to the wrong address | `MAIL_TO` isn't set in `.env`; it's falling back to the defaults in `backend/notifier.py` |
| One company shows red in Debug | That site changed its API. Other sources are unaffected; see *Known quirks* |
| No new jobs for hours | Expected if nothing was posted. Confirm the source timestamps are advancing in the Debug sidebar |
| `Port 8000 is already in use` | A previous server is still running. Find it with `netstat -ano \| findstr :8000` and end that PID in Task Manager |

---

## Project layout

```
backend/
  main.py            FastAPI app, API routes, hourly scheduler
  poller.py          Runs every adapter, dedupes, triggers email
  config.py          Company list + poll interval
  db.py              SQLite schema and queries
  notifier.py        SMTP email alerts
  documents.py       Per-application folder management
  adapters/
    base.py          Keyword filters + shared job normalization
    greenhouse.py    …one module per ATS platform
    custom.py        Amazon, Uber, Microsoft, Apple, Google
    github_newgrad.py
frontend/
  index.html         The entire dashboard UI (no build step)
```

---

## Privacy

Everything runs locally. The database, your documents and your credentials never leave your machine. The only outbound traffic is the polling requests to each company's public careers API, and the SMTP connection that sends your own alerts to yourself.
