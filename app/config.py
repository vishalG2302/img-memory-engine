import os
from dotenv import load_dotenv

load_dotenv()  # <-- THIS LINE IS CRITICAL

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    UPLOAD_FOLDER = "uploads"

settings = Settings()