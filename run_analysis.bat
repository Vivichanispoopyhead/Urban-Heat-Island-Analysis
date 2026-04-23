@echo off
setlocal

cd /d "%~dp0"
set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [INFO] Creating virtual environment...
    py -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Could not create virtual environment.
        exit /b 1
    )
)

echo [INFO] Installing/updating required packages...
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    exit /b 1
)

echo [INFO] Running command-line analysis...
"%PYTHON%" analysis.py

endlocal
