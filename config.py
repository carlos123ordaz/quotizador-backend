import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    MONGODB_URL = os.getenv("MONGODB_URL")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")
    AZURE_STORAGE_CONTAINER = os.getenv(
        "AZURE_STORAGE_CONTAINER", "quotizador")
    BITRIX24_BASE_URL = os.getenv(
        "BITRIX24_BASE_URL", "https://corsusaint.bitrix24.com/rest/4296/gzwh0355xyw5ihbc")

    TEMP_FOLDER = "./temp"
    MAX_WORKERS = os.cpu_count() - 1 if os.cpu_count() > 1 else 1

    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]


settings = Settings()

os.makedirs(settings.TEMP_FOLDER, exist_ok=True)
