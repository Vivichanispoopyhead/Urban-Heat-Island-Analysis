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

echo [INFO] Starting Urban Heat Island web app...
echo [INFO] Open http://localhost:8501 in your browser.
set "STREAMLIT_BROWSER_GATHER_USAGE_STATS=false"
start "" http://localhost:8501
"%PYTHON%" -m streamlit run web_app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

endlocal
