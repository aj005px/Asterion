# Asterion ML Evaluation Report

Generated: 2026-10-25T00:00:00.000000 (updated for hybrid architecture)

## Data Pipeline
- Chrome extension tracks tab activation and duration
- Events sent to FastAPI endpoints (/tab/activate, /tab/duration)
- Stored in MongoDB (collections: tab_events, feedback)
- Features extracted by domain aggregation
- **Hybrid ranking (v2)**: Baseline weighted scoring preserved; ML model blends with baseline at inference time

## Baseline Scoring Formula (preserved)
```
time_score = log1p(total_time) / max(log1p(total_time))
activation_score = log1p(activation_count) / max(log1p(activation_count))
recency_score = exp(-recency_seconds / 1800)
weighted_score = 0.40*time_score + 0.35*activation_score + 0.25*recency_score
```

## Hybrid Architecture (implemented)
- **Model**: Logistic Regression with StandardScaler (Pipeline) - reused as in existing training approach
- **Training features** (must match inference): `time_score`, `activation_score`, `recency_score`, `weighted_score`
- **Target**: Genuine user feedback labels `useful` / `not_useful` (historical supervision only). Feedback labels are **not** used as inference-time inputs.
- **Training data**: Only genuine eligible feedback (filters: `scoring_version == "v2"`, excludes `is_test == True`, excludes `test.example`, validates features/range/timestamp). No synthetic/training-on-inference data; no leakage.
- **Split**: Chronological (70/30) to prevent temporal leakage.
- **Inference**: Load trained model; predict probability of usefulness P(useful). Compute hybrid score as `baseline_weight * weighted_score + ml_weight * P(useful)`, normalized/bounded in [0,1]. Higher score = higher priority.
- **Fallback**: If model missing/stale/invalid/unloaded or insufficient trustworthy training data, **baseline-only** ranking is used automatically with no errors. `GET /recommendations` includes `model_status` and indicates `ml_used` per item.
- **Safety**: Never auto-closes tabs; only recommendations for review. Pinned/active/audible/internal pages excluded. Explicit user action required for closing.

## Data Validation
- Feedback validated on export (`validate_record`); invalid records excluded
- Test records (is_test flag or test.example) excluded from training
- Incomplete/invalid feature snapshots not converted to valid training examples
- Feature values clamped/validated; missing values handled safely

## Training
- Current environment state: Model files may not exist if insufficient genuine data collected.
- When trained, coefficients/intercept and metrics are saved to `intelligence/models/asterion_logreg_metadata.json`.
- Minimum thresholds are enforced (insufficient data/diversity -> no model trained; baseline remains active).

## Evaluation Results
*Status depends on local data.* Model training is only performed if sufficient genuine v2 feedback with both classes exists. This report documents the implemented hybrid pipeline; measured real-world performance requires genuine user feedback in the local MongoDB instance.

## Limitations
- Requires genuine user feedback to train a reliable model
- Small sample sizes limit generalization
- Baseline remains active until a valid trained model is available
- Local-only operation

## Reproduce
```bash
cd ~/Desktop/projects/Asterion
source .venv/bin/activate
python intelligence/export_feedback.py
python intelligence/check_feedback.py
python intelligence/train_model.py  # trains only if sufficient genuine data
python generate_report.py
```

## Implemented vs Future Work
- **Implemented**: Genuine hybrid ML ranking with safe baseline fallback, feature consistency, no inference-time feedback leakage, chronological validation, deterministic/bounded scoring, API/model status reporting, tests for hybrid behavior.
- **Future work**: Larger-scale evaluation, additional features if warranted, model calibration/monitoring - only if supported by sufficient genuine data.

