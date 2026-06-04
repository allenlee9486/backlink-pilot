@echo off
setlocal
cd /d "%~dp0"
echo ------------------------------------------------
echo [STARTING] Backlink Pilot Local Mode
echo ------------------------------------------------
echo.
echo [1/3] Initializing Browser Daemon...
start /b bb-browser daemon start
timeout /t 3 > nul

echo [2/3] Opening Local Browser Window...
bb-browser open about:blank

echo.
echo ------------------------------------------------
echo [ACTION REQUIRED]
echo 1. Check if a browser window opened.
echo 2. If YES, press any key to start the task.
echo 3. If NO, ensure Chrome is installed and try again.
echo ------------------------------------------------
pause

echo.
echo [3/3] Executing Task: node src/batch-submit.js 20
node src/batch-submit.js 20

echo.
echo [FINISHED] Task completed.
pause
