@echo off
setlocal

cd /d "%~dp0"

set "PYTHON="
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
if not defined PYTHON if exist "venv\Scripts\python.exe" set "PYTHON=venv\Scripts\python.exe"

if not defined PYTHON (
    where py >nul 2>&1
    if not errorlevel 1 set "PYTHON=py"
)

if not defined PYTHON (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON=python"
)

if not defined PYTHON (
    echo Python was not found.
    echo Install Python 3.10 or newer, then run this file again.
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo requirements.txt was not found in:
    echo %CD%
    pause
    exit /b 1
)

echo Starting NyayaAI at http://127.0.0.1:5000
start "" "http://127.0.0.1:5000"
"%PYTHON%" app.py

if errorlevel 1 (
    echo.
    echo NyayaAI stopped because an error occurred.
    pause
)

endlocal
