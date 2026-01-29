import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    app_name: str = "Vau API"
    app_version: str = "1.0.0"
    debug: bool = True
    
    def __init__(self):
        # Load from environment variables - WITH .env SUPPORT
        self.app_name = os.getenv("APP_NAME", "Vau API")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        self.mongodb_url = os.getenv("MONGODB_URL", "")
        self.database_url = os.getenv("DATABASE_URL", "")
        self.database_name = os.getenv("DATABASE_NAME", "vau_db")
        
        # Security
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = os.getenv("ALGORITHM", "HS256")
        access_token_env = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
        self.access_token_expire_minutes = int(access_token_env) if access_token_env else 30
        
        # Cloudinary - LOAD FROM .env FILE
        self.cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
        self.cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY", "")
        self.cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET", "")
        self.cloudinary_upload_preset = os.getenv("CLOUDINARY_UPLOAD_PRESET", "vau_media_uploads")
        
        # File upload
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        max_file_env = os.getenv("MAX_FILE_SIZE")
        self.max_file_size = int(max_file_env) if max_file_env else 100 * 1024 * 1024

settings = Settings()
