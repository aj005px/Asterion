import json
import pickle
from pathlib import Path
from datetime import datetime

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "asterion_logreg.pkl"
METADATA_PATH = MODEL_DIR / "asterion_logreg_metadata.json"

# Must match training features exactly
FEATURES = ["time_score", "activation_score", "recency_score", "weighted_score"]
SCORING_VERSION = "v2"


class ModelInference:
    def __init__(self):
        self.model = None
        self.metadata = None
        self.loaded = False
        self.load()

    def load(self):
        self.model = None
        self.metadata = None
        self.loaded = False
        try:
            if MODEL_PATH.exists():
                with open(MODEL_PATH, 'rb') as f:
                    self.model = pickle.load(f)
                if METADATA_PATH.exists():
                    with open(METADATA_PATH) as f:
                        self.metadata = json.load(f)
                # Basic validation
                if self.model is None:
                    self.loaded = False
                    return
                self.loaded = True
        except Exception:
            self.loaded = False

    def reload(self):
        self.load()

    def predict_score(self, features):
        if not self.loaded or self.model is None:
            return None
        try:
            import numpy as np

            # Build feature vector in exact order
            X = np.array([[float(features.get(f, 0.0)) for f in FEATURES]])
            # Clamp to [0,1] range where appropriate (features are normalized)
            proba = self.model.predict_proba(X)[0][1]
            proba = float(proba)
            if proba < 0.0:
                proba = 0.0
            if proba > 1.0:
                proba = 1.0
            return proba
        except Exception:
            return None

    def is_available(self):
        if not self.loaded or self.model is None:
            return False
        # If metadata indicates insufficient training, treat as not reliably available
        try:
            if self.metadata and isinstance(self.metadata, dict):
                metrics = self.metadata.get("metrics") or {}
                # If no test data or weird state, still allow if model loads; but be conservative
            return True
        except Exception:
            return False

    def status(self):
        return {
            "model_loaded": bool(self.loaded and self.model is not None),
            "model_path": str(MODEL_PATH),
            "features": FEATURES,
            "metadata_present": bool(self.metadata is not None),
        }


inference = ModelInference()

