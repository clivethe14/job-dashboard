@echo off
cd /d "D:\Documents\Claude\Job Dashbaord"

REM Start the server in the background (pythonw = no console window).
start "" ".venv\Scripts\pythonw.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

REM Give the server a moment to come up, then open the dashboard in the browser.
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8000"
