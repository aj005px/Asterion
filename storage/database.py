from datetime import datetime, timezone
from urllib.parse import urlparse
import os

from pymongo import MongoClient

try:
    from config import get_mongo_uri, get_mongo_db_name
    MONGO_URI = get_mongo_uri()
    DB_NAME = get_mongo_db_name()
except Exception:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME = os.getenv("MONGO_DB_NAME", "asterion")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)

db = client[DB_NAME]
tab_events = db["tab_events"]
feedback_events = db["feedback"]


def connect_to_mongodb():
    try:
        client.admin.command("ping")
        tab_events.create_index([("url", 1), ("timestamp", -1)])
        tab_events.create_index([("domain", 1), ("timestamp", -1)])
        tab_events.create_index([("session_id", 1), ("tab_id", 1)])
        feedback_events.create_index([("domain", 1), ("timestamp", -1)])
        print("Connected to MongoDB!")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        raise


def save_tab_event(url: str, tab_id: int = None, session_id: str = None):
    try:
        domain = urlparse(url).hostname
        if not domain:
            domain = url
    except Exception:
        domain = None

    event = {
        "url": url,
        "domain": domain,
        "event_type": "activate",
        "tab_id": tab_id,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc),
        "is_test": False,
    }

    result = tab_events.insert_one(event)
    return str(result.inserted_id)


def save_tab_duration(
    url: str,
    tab_id: int = None,
    session_id: str = None,
    duration_seconds: float = 0,
):
    try:
        domain = urlparse(url).hostname
        if not domain:
            domain = url
    except Exception:
        domain = None

    event = {
        "url": url,
        "domain": domain,
        "tab_id": tab_id,
        "session_id": session_id,
        "event_type": "duration",
        "duration_seconds": float(duration_seconds) if duration_seconds is not None else 0,
        "timestamp": datetime.now(timezone.utc),
        "is_test": False,
    }

    result = tab_events.insert_one(event)
    return str(result.inserted_id)


def save_feedback(
    domain: str,
    label: str,
    weighted_score: float,
    time_score: float,
    activation_score: float,
    recency_score: float,
    scoring_version: str = "v2",
    is_test: bool = False,
    feature_snapshot: dict = None,
):
    event = {
        "domain": domain,
        "label": label,
        "weighted_score": float(weighted_score),
        "time_score": float(time_score),
        "activation_score": float(activation_score),
        "recency_score": float(recency_score),
        "scoring_version": scoring_version,
        "timestamp": datetime.now(timezone.utc),
        "is_test": bool(is_test),
    }
    if feature_snapshot is not None:
        event["feature_snapshot"] = feature_snapshot

    result = feedback_events.insert_one(event)
    return str(result.inserted_id)
