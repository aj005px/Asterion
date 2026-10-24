# Asterion ML Evaluation Report

Generated: 2026-10-24T23:04:29.758016

## Data Pipeline
- Chrome extension tracks tab activation and duration
- Events sent to FastAPI endpoints (/tab/activate, /tab/duration)
- Stored in MongoDB (collections: tab_events, feedback)
- Features extracted by domain aggregation
- Ranking via weighted baseline (v2)

## Baseline Scoring Formula
```
time_score = log1p(total_time) / max(log1p(total_time))
activation_score = log1p(activation_count) / max(log1p(activation_count))
recency_score = exp(-recency_seconds / 1800)
weighted_score = 0.40*time_score + 0.35*activation_score + 0.25*recency_score
```

## Data Validation
- Feedback validated on export; invalid records excluded
- Test records (is_test flag or test.example) excluded from training
- Incomplete feature snapshots not converted to valid training examples

## Training
- Model: Logistic Regression with StandardScaler (explainable)
- Features: time_score, activation_score, recency_score, weighted_score
- Split: Chronological (70/30) to prevent leakage
- Genuine eligible samples: 6

## Evaluation Results
Model not trained - insufficient genuine data.

## Limitations
- Requires genuine user feedback to train
- Small sample sizes limit generalization
- Baseline remains active until model validated
- Local-only operation

## Reproduce
```bash
cd ~/Desktop/projects/Asterion
source .venv/bin/activate
python intelligence/export_feedback.py
python intelligence/check_feedback.py
python intelligence/train_model.py
python generate_report.py
```
