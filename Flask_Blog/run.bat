@echo off
REM --- Setup Virtual Environment ---
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM --- Activate Virtual Environment ---
echo Activating virtual environment...
cd /d "%~dp0"
CALL venv\Scripts\activate.bat

REM --- Install requirements and run app within the venv ---
echo Installing required libraries from requirements.txt...
pip install -r requirements.txt

echo Booting up website with localhost...
python run.py

echo Script finished.
pause