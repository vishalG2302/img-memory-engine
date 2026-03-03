import os
from dotenv import load_dotenv

load_dotenv()  # <-- THIS LINE IS CRITICAL

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    UPLOAD_FOLDER = "uploads"

settings = Settings()