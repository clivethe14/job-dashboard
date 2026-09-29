@echo off
REM Silent launcher used by the Startup shortcut at login: starts the server
REM hidden in the background (no console, no browser). Open http://127.0.0.1:8000
REM yourself whenever you want to view the dashboard.
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Documents\Claude\Job Dashbaord\start_server.ps1"
