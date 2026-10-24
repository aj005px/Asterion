"""
Hybrid ML ranking for Asterion.
- Preserves baseline weighted scoring (time 40%, activation 35%, recency 25%) intact.
- Uses baseline scores + activity features as inputs to LogisticRegression with StandardScaler.
- Model is trained on genuine Useful/Not useful feedback only (historical supervision).
- At inference, blends ML predicted probability of usefulness with baseline score.
- Falls back to baseline-only if model missing/stale/invalid/insufficient data.
- Never trains on inference outputs; features match inference exactly.
- Deterministic, bounded [0,1], higher score = higher priority.
"""
import math
from typing import List, Dict, Any, Optional

from intelligence.features import get_domain_features
from intelligence.inference import inference
from config import HYBRID_ML_WEIGHT, HYBRID_BASELINE_WEIGHT


def _compute_baseline_for_domain(d: Dict[str, Any], time_values_log1p: List[float], act_values_log1p: List[float],
                                 max_time: float, max_act: float) -> Dict[str, Any]:
    recency = d.get("recency_seconds")
    t_log = math.log1p(float(d.get("total_time_seconds") or 0.0))
    a_log = math.log1p(float(d.get("activation_count") or 0))
    time_score = t_log / max_time if max_time else 0.0
    activation_score = a_log / max_act if max_act else 0.0
    if recency is not None:
        recency_score = math.exp(-float(recency) / 1800.0)
    else:
        recency_score = 0.0
    # Clamp
    time_score = max(0.0, min(1.0, time_score))
    activation_score = max(0.0, min(1.0, activation_score))
    recency_score = max(0.0, min(1.0, recency_score))
    weighted_score = (
        0.40 * time_score
        + 0.35 * activation_score
        + 0.25 * recency_score
    )
    weighted_score = max(0.0, min(1.0, weighted_score))
    return {
        "time_score": round(time_score, 6),
        "activation_score": round(activation_score, 6),
        "recency_score": round(recency_score, 6),
        "weighted_score": round(weighted_score, 6),
    }


def compute_hybrid_scores() -> List[Dict[str, Any]]:
    domains = get_domain_features()
    if not domains:
        return []

    # Compute log1p values for normalization (same as baseline)
    time_values_log1p = [math.log1p(float(d.get("total_time_seconds") or 0.0)) for d in domains]
    act_values_log1p = [math.log1p(float(d.get("activation_count") or 0)) for d in domains]
    max_time = max(time_values_log1p) if time_values_log1p else 0.0
    max_act = max(act_values_log1p) if act_values_log1p else 0.0

    results = []
    model_available = inference.is_available()

    for d in domains:
        base = _compute_baseline_for_domain(d, time_values_log1p, act_values_log1p, max_time, max_act)
        ml_prob = None
        if model_available:
            # Features for inference must match training exactly
            feat_infer = {
                "time_score": base["time_score"],
                "activation_score": base["activation_score"],
                "recency_score": base["recency_score"],
                "weighted_score": base["weighted_score"],
            }
            ml_prob = inference.predict_score(feat_infer)
            if ml_prob is not None:
                ml_prob = max(0.0, min(1.0, float(ml_prob)))

        # Determine hybrid score
        if ml_prob is not None and model_available:
            # Blend: higher predicted usefulness -> higher priority
            hybrid = HYBRID_BASELINE_WEIGHT * base["weighted_score"] + HYBRID_ML_WEIGHT * ml_prob
            hybrid = max(0.0, min(1.0, hybrid))
            ranking_method = "hybrid_ml_baseline"
            ml_used = True
        else:
            hybrid = base["weighted_score"]  # fallback to baseline
            ranking_method = "weighted_baseline"
            ml_used = False

        results.append({
            "domain": d["domain"],
            "time_score": round(base["time_score"], 3),
            "activation_score": round(base["activation_score"], 3),
            "recency_score": round(base["recency_score"], 3),
            "weighted_score": round(base["weighted_score"], 3),
            "ml_probability": round(ml_prob, 3) if ml_prob is not None else None,
            "hybrid_score": round(hybrid, 3),
            "ml_used": ml_used,
            "ranking_method": ranking_method,
        })

    results.sort(key=lambda item: item["hybrid_score"], reverse=True)
    return results
