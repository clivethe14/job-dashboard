# Launches the Job Dashboard server hidden in the background.
# pythonw.exe has no console, so its stdout/stderr MUST be redirected to files
# or the process crashes the moment the server writes its first log line.
$root = 'D:\Documents\Claude\Job Dashbaord'
if (-not (Test-Path "$root\logs")) { New-Item -ItemType Directory -Path "$root\logs" | Out-Null }

# Don't start a second copy if the server is already listening on port 8000.
$busy = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($busy) { Write-Host "Already running (PID $($busy.OwningProcess))."; return }

Start-Process -WindowStyle Hidden `
  -WorkingDirectory $root `
  -FilePath "$root\.venv\Scripts\pythonw.exe" `
  -ArgumentList '-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000' `
  -RedirectStandardOutput "$root\logs\server_console.log" `
  -RedirectStandardError "$root\logs\server_error.log"

Write-Host "Job Dashboard server starting..."
