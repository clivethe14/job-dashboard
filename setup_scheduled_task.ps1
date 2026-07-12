# Run this in a normal PowerShell window (not from Claude Code's sandboxed shell).
# Registers a task that starts the Job Dashboard silently at logon.

$action = New-ScheduledTaskAction -Execute "D:\Documents\Claude\Job Dashbaord\start_dashboard.bat" -WorkingDirectory "D:\Documents\Claude\Job Dashbaord"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask -TaskName "JobDashboard" -Action $action -Trigger $trigger -Settings $settings -Description "Runs the local job-posting dashboard (FastAPI) at logon"

Write-Host "Task registered. It will start automatically next time you log on."
Write-Host "To start it right now without logging off, run:"
Write-Host "  Start-ScheduledTask -TaskName JobDashboard"
