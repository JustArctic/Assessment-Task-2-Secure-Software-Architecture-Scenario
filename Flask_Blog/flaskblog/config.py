import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from a .env file into the system environment

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