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
