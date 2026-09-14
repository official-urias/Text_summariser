@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [Environment]::GetFolderPath('Desktop'); $shortcut = $ws.CreateShortcut(\"$desktop\\AI Text Summarizer.lnk\"); $shortcut.TargetPath = '%~dp0run.bat'; $shortcut.WorkingDirectory = '%~dp0'; $shortcut.Description = 'AI Text Summarizer'; $shortcut.Save(); Write-Host 'Desktop shortcut created successfully!' -ForegroundColor Green"
pause
