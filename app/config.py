import os
from dotenv import load_dotenv

load_dotenv()  # <-- THIS LINE IS CRITICAL

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    UPLOAD_FOLDER = "uploads"

settings = Settings()