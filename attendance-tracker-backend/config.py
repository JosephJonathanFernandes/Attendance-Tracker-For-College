import os
from datetime import timedelta

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-this-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///attendance.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-this-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)  # Tokens expire in 7 days
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # Refresh tokens expire in 30 days
    
    # CORS configuration
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    
    # Email configuration (for notifications - optional)
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "1", "on"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    
    # Timezone
    TIMEZONE = os.environ.get("TIMEZONE", "UTC")
    
    # Pagination defaults
    ITEMS_PER_PAGE = 20
    MAX_ITEMS_PER_PAGE = 100
