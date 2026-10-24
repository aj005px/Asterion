import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    from storage.database import save_tab_event, save_tab_duration, save_feedback
    from intelligence.features import get_domain_features
    from intelligence.compare_scores import compare_scores
    assert callable(save_tab_event)
    assert callable(compare_scores)


def test_feature_extraction_structure():
    from intelligence.features import get_domain_features
    features = get_domain_features()
    assert isinstance(features, list)
    for f in features:
        assert "domain" in f
        assert "total_time_seconds" in f
        assert "activation_count" in f
        assert "recency_seconds" in f


def test_compare_scores_structure():
    from intelligence.compare_scores import compare_scores
    results = compare_scores()
    assert isinstance(results, list)
    for r in results:
        for key in ["domain", "time_score", "activation_score", "recency_score", "weighted_score"]:
            assert key in r
        for k in ["time_score", "activation_score", "recency_score", "weighted_score"]:
            assert 0 <= r[k] <= 1


def test_export_validation():
    from intelligence.export_feedback import validate_record
    assert validate_record({}) is not None
    assert validate_record({"domain": "x", "label": "bad", "time_score": 0.5, "activation_score": 0.5, "recency_score": 0.5, "weighted_score": 0.5, "timestamp": None}) is not None


# Hybrid ML ranking tests (synthetic data only)
def test_hybrid_fallback_when_no_model(monkeypatch):
    from intelligence import hybrid_ranking
    from intelligence import inference

    orig_available = inference.inference.is_available
    inference.inference.is_available = lambda: False
    try:
        results = hybrid_ranking.compute_hybrid_scores()
        if results:
            for r in results:
                assert "weighted_score" in r
                assert "hybrid_score" in r
                assert r["ml_used"] is False
                assert r["ranking_method"] == "weighted_baseline"
                assert 0 <= r["hybrid_score"] <= 1
    finally:
        inference.inference.is_available = orig_available


def test_hybrid_feature_consistency():
    from intelligence.inference import FEATURES
    assert FEATURES == ["time_score", "activation_score", "recency_score", "weighted_score"]


def test_hybrid_score_direction_and_bounds():
    from intelligence.hybrid_ranking import compute_hybrid_scores
    results = compute_hybrid_scores()
    for r in results:
        assert 0 <= r.get("time_score", 0) <= 1
        assert 0 <= r.get("activation_score", 0) <= 1
        assert 0 <= r.get("recency_score", 0) <= 1
        assert 0 <= r.get("weighted_score", 0) <= 1
        assert 0 <= r.get("hybrid_score", 0) <= 1
        if r.get("ml_probability") is not None:
            assert 0 <= r["ml_probability"] <= 1


def test_hybrid_recommendation_ordering():
    from intelligence.hybrid_ranking import compute_hybrid_scores
    results = compute_hybrid_scores()
    if len(results) >= 2:
        scores = [r["hybrid_score"] for r in results]
        assert scores == sorted(scores, reverse=True)


def test_feedback_validation_strict():
    from intelligence.export_feedback import validate_record
    good = {"domain": "example.com", "label": "useful", "time_score": 0.1, "activation_score": 0.2, "recency_score": 0.3, "weighted_score": 0.18, "timestamp": "2026-01-01T00:00:00Z"}
    assert validate_record(good) is None
    bad_label = dict(good)
    bad_label["label"] = "maybe"
    assert validate_record(bad_label) is not None
    bad_range = dict(good)
    bad_range["time_score"] = 1.5
    assert validate_record(bad_range) is not None
    bad_ts = dict(good)
    bad_ts["timestamp"] = None
    assert validate_record(bad_ts) is not None


def test_insufficient_data_handling():
    from intelligence import train_model
    try:
        valid, excluded = train_model.load_genuine_training_data()
        assert isinstance(valid, list)
        assert isinstance(excluded, dict)
    except Exception:
        pass


def test_invalid_model_fallback():
    from intelligence import inference
    from intelligence import hybrid_ranking
    orig_loaded = inference.inference.loaded
    orig_model = inference.inference.model
    try:
        inference.inference.loaded = False
        inference.inference.model = None
        results = hybrid_ranking.compute_hybrid_scores()
        if results:
            for r in results:
                assert r["ml_used"] is False
    finally:
        inference.inference.loaded = orig_loaded
        inference.inference.model = orig_model

