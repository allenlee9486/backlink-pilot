@echo off
setlocal
echo ==========================================
echo    BACKLINK PILOT - STARTING...
echo ==========================================

:: Change to the script's directory
cd /d "%~dp0"

echo [DEBUG] Current Directory: %cd%

:: Check if Node is installed
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    pause
    exit /b 1
)

:: Check if node_modules exists
if not exist "node_modules\" (
    echo [INFO] node_modules not found. Installing dependencies...
    npm install
)

echo [INFO] Starting submission task (20 items)...
echo [INFO] A browser window should open shortly.
echo.

node src/batch-submit.js 20

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Script exited with error code %ERRORLEVEL%
) else (
    echo.
    echo [SUCCESS] Submission batch finished.
)

echo.
echo Press any key to exit.
pause > nul
