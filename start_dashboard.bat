@echo off
REM Starts the Job Dashboard server (hidden) and opens it in your browser.
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Documents\Claude\Job Dashbaord\start_server.ps1"

REM Give the server a few seconds to come up, then open the dashboard.
timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:8000"
