@echo off
echo ================================================================================
echo TDS/TCS ANALYZER - Starting Application
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo Installing required packages...
pip install -r requirements.txt

echo.
echo Starting TDS/TCS Analyzer...
echo Open your browser and go to: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python tds_web_app.py

pause
