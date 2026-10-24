import json
import pickle
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "asterion_logreg.pkl"
METADATA_PATH = MODEL_DIR / "asterion_logreg_metadata.json"

FEATURES = ["time_score", "activation_score", "recency_score", "weighted_score"]


class ModelInference:
    def __init__(self):
        self.model = None
        self.metadata = None
        self.loaded = False
        self.load()
    
    def load(self):
        try:
            if MODEL_PATH.exists():
                with open(MODEL_PATH, 'rb') as f:
                    self.model = pickle.load(f)
                if METADATA_PATH.exists():
                    with open(METADATA_PATH) as f:
                        self.metadata = json.load(f)
                self.loaded = True
        except Exception as e:
            self.loaded = False
    
    def predict_score(self, features):
        if not self.loaded or self.model is None:
            return None
        try:
            import numpy as np
            X = np.array([[features.get(f, 0) for f in FEATURES]])
            proba = self.model.predict_proba(X)[0][1]
            return float(proba)
        except Exception:
            return None
    
    def is_available(self):
        return self.loaded and self.model is not None


inference = ModelInference()
