import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except Exception:
    pass


def get_mongo_uri():
    uri = os.getenv("MONGO_URI")
    if not uri:
        raise ValueError("MONGO_URI not set in environment or .env file")
    return uri


def get_mongo_db_name():
    return os.getenv("MONGO_DB_NAME", "asterion")


def get_api_host():
    return os.getenv("API_HOST", "127.0.0.1")


def get_api_port():
    return int(os.getenv("API_PORT", "8000"))
