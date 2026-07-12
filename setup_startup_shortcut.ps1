# Run this in a normal PowerShell window.
# Adds a shortcut to your Startup folder so the Job Dashboard launches
# automatically at logon -- no Task Scheduler / admin rights needed.

$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "JobDashboard.lnk"
# Silent launcher: starts the server at login without popping open a browser tab.
$targetPath = "D:\Documents\Claude\Job Dashbaord\start_dashboard_silent.bat"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = "D:\Documents\Claude\Job Dashbaord"
$shortcut.WindowStyle = 7  # minimized
$shortcut.Description = "Starts the local Job Dashboard"
$shortcut.Save()

Write-Host "Shortcut created at: $shortcutPath"
Write-Host "It will run automatically next time you log on."
Write-Host ""
Write-Host "To start it right now without logging off, run:"
Write-Host "  Start-Process `"$targetPath`""
