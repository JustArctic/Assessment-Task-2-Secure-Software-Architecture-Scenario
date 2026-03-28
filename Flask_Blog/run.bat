@echo off
cd /d "%~dp0"

echo ============================================
echo   Flask Project Setup with HTTPS (mkcert)
echo ============================================

REM --- Check for mkcert.exe ---
if not exist mkcert.exe (
    echo ERROR: mkcert.exe not found!
    echo Please place mkcert.exe in the same folder as this script.
    pause
    exit /b
)

REM --- Setup Virtual Environment ---
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM --- Activate Virtual Environment ---
echo Activating virtual environment...
CALL venv\Scripts\activate.bat

REM --- Install requirements ---
echo Installing required libraries from requirements.txt...
pip install -r requirements.txt

REM --- Create certs folder if missing ---
if not exist certs (
    mkdir certs
)

REM --- Install mkcert local CA (only needed once per machine) ---
echo Installing mkcert local Certificate Authority...
mkcert.exe -install

REM --- Generate SSL certificates ---
echo Generating SSL certificate...
mkcert.exe -cert-file certs\cert.pem -key-file certs\key.pem localhost

REM --- Set environment variables ---
echo Setting environment variables...
set FLASK_APP=flaskblog.py
set FLASK_ENV=production
set SECRET_KEY=mysupersecretkey
set FERNET_KEY=mysuperdupersecretkey
set SQLALCHEMY_DATABASE_URI=sqlite:///site.db
set EMAIL_USER=your_email_here
set EMAIL_PASS=your_password_here

REM --- Set variables that control admin privileges ---
echo Granting admin privileges to operator users...
set ADMIN_EMAIL=admin@gmail.com
set ADMIN_PASSWORD=admin

REM --- Run Flask app with HTTPS ---
echo Starting Flask app with HTTPS...
python run.py

echo Script finished.
pause