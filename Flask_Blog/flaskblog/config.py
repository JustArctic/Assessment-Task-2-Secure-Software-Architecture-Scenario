import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') # Secret key used by Flask for session security and CSRF protection
    FERNET_KEY = os.environ.get('FERNET_KEY') # Secret key used by Cryptography to encrypt and decrypt user emails
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') # Database connection string for SQLAlchemy

    # Mail server configuration for sending emails (using Gmail SMTP)
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True

    # Email account credentials pulled from environment variables
    MAIL_USERNAME = os.environ.get('EMAIL_USER')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')

    # Strengthen session management with cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True # Only over HTTPS
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # Set session timeout to 1 hour
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)