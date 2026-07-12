@echo off
REM Silent launcher used by the Startup shortcut at login: starts the server
REM in the background (no console, no browser). Open http://127.0.0.1:8000
REM yourself whenever you want to view the dashboard.
cd /d "D:\Documents\Claude\Job Dashbaord"
start "" ".venv\Scripts\pythonw.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
