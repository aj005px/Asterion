#!/usr/bin/env python3
import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix, roc_auc_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from intelligence.export_feedback import export_feedback, validate_record
from storage.database import feedback_events

FEATURES = ["time_score", "activation_score", "recency_score", "weighted_score"]
MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "asterion_logreg.pkl"
METADATA_PATH = MODEL_DIR / "asterion_logreg_metadata.json"


def load_genuine_training_data():
    records = list(feedback_events.find().sort("timestamp", 1))
    valid = []
    excluded = {"test_flag": 0, "invalid": 0, "test_domain": 0}
    
    TEST_DOMAINS = {"test.example"}
    
    for rec in records:
        err = validate_record(rec)
        if err:
            excluded["invalid"] += 1
            continue
        if rec.get("is_test") is True:
            excluded["test_flag"] += 1
            continue
        if rec.get("domain") in TEST_DOMAINS:
            excluded["test_domain"] += 1
            continue
        if rec.get("scoring_version") != "v2":
            continue  # focus on current version per requirements
        
        valid.append(rec)
    
    return valid, excluded


def train():
    valid, excluded = load_genuine_training_data()
    
    print("Asterion Model Training")
    print("=" * 40)
    print(f"Genuine eligible records: {len(valid)}")
    print(f"Excluded - test flag: {excluded['test_flag']}, test domain: {excluded['test_domain']}, invalid: {excluded['invalid']}")
    
    if len(valid) < 20:
        print("\nInsufficient genuine data for training.")
        print("Need at least 20 eligible labeled examples from real feedback.")
        print("Model not trained. Baseline will remain active.")
        return {"trained": False, "reason": "insufficient_data", "eligible": len(valid)}
    
    df = pd.DataFrame(valid)
    if df["label"].nunique() < 2:
        print("\nInsufficient class diversity.")
        print("Need both 'useful' and 'not_useful' labels.")
        return {"trained": False, "reason": "insufficient_diversity", "eligible": len(valid)}
    
    X = df[FEATURES].values
    y = (df["label"] == "useful").astype(int)
    
    # Chronological split to avoid leakage
    n = len(df)
    split = int(n * 0.7)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000, random_state=42))
    ])
    
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    y_proba = pipe.predict_proba(X_test)[:, 1] if len(X_test) > 0 else []
    
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary', zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    
    metrics = {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "confusion_matrix": cm.tolist(),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "evaluation_method": "chronological_split",
    }
    
    try:
        if len(set(y_test)) > 1 and len(y_proba) > 0:
            metrics["roc_auc"] = float(roc_auc_score(y_test, y_proba))
    except Exception:
        pass
    
    # Save model
    import pickle
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(pipe, f)
    
    metadata = {
        "trained_at": datetime.now().isoformat(),
        "features": FEATURES,
        "model_type": "LogisticRegression",
        "metrics": metrics,
        "eligible_samples": len(valid),
        "excluded": excluded,
        "coefficients": pipe.named_steps['clf'].coef_[0].tolist(),
        "intercept": float(pipe.named_steps['clf'].intercept_[0]),
    }
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\nTraining complete")
    print(f"Model saved: {MODEL_PATH}")
    print(f"Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")
    print(f"Confusion matrix: {cm.tolist()}")
    
    return {"trained": True, "metrics": metrics, "metadata": metadata}


if __name__ == "__main__":
    train()
