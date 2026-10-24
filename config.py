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


# Hybrid ML ranking configuration
# Baseline weighted: time 40%, activation 35%, recency 25% (preserved)
HYBRID_ML_WEIGHT = float(os.getenv("ASTERION_HYBRID_ML_WEIGHT", "0.5"))
# Clamp to safe range
if HYBRID_ML_WEIGHT < 0.0:
    HYBRID_ML_WEIGHT = 0.0
if HYBRID_ML_WEIGHT > 1.0:
    HYBRID_ML_WEIGHT = 1.0

HYBRID_BASELINE_WEIGHT = float(os.getenv("ASTERION_HYBRID_BASELINE_WEIGHT", str(1.0 - HYBRID_ML_WEIGHT)))
if HYBRID_BASELINE_WEIGHT < 0.0:
    HYBRID_BASELINE_WEIGHT = 0.0
if HYBRID_BASELINE_WEIGHT > 1.0:
    HYBRID_BASELINE_WEIGHT = 1.0

# Require minimum training data quality
MIN_TRAINING_SAMPLES = int(os.getenv("ASTERION_MIN_TRAINING_SAMPLES", "20"))
MIN_TRAINING_CLASSES = int(os.getenv("ASTERION_MIN_TRAINING_CLASSES", "2"))

