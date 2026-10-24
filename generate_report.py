#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

from storage.database import tab_events, feedback_events

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
HTML_PATH = REPORTS_DIR / "asterion_statistics.html"
MD_PATH = REPORTS_DIR / "ASTERION_ML_EVALUATION.md"


def count_collection(coll):
    try:
        return coll.count_documents({})
    except Exception:
        return 0


def generate():
    total_events = count_collection(tab_events)
    total_feedback = count_collection(feedback_events)
    
    try:
        feedback_list = list(feedback_events.find({}))
    except Exception:
        feedback_list = []
    
    valid_feedback = 0
    test_feedback = 0
    incomplete = 0
    for f in feedback_list:
        if f.get("is_test"):
            test_feedback += 1
            continue
        if f.get("label") in ["useful", "not_useful"] and all(k in f for k in ["time_score", "activation_score", "recency_score", "weighted_score"]):
            valid_feedback += 1
        else:
            incomplete += 1
    
    # Try to load model metadata
    model_meta = None
    try:
        meta_path = Path(__file__).parent / "intelligence" / "models" / "asterion_logreg_metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                model_meta = json.load(f)
    except Exception:
        pass
    
    timestamp = datetime.now().isoformat()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Asterion Statistics Report</title>
    <style>
        :root {{
            --bg: #0a0a1a; --bg2: #12123a; --cyan: #00ffff; --mag: #ff00ff; --green: #00ff88; --text: #e0e0ff; --dim: #a0a0c0;
        }}
        body {{
            font-family: 'Courier New', monospace;
            background: linear-gradient(180deg, var(--bg) 0%, #0f0f2e 100%);
            color: var(--text);
            margin: 0; padding: 20px;
            line-height: 1.6;
        }}
        header {{
            border: 2px solid var(--cyan);
            padding: 20px;
            background: linear-gradient(90deg, var(--bg2) 0%, #1a1a4a 100%);
            box-shadow: 0 0 10px rgba(0,255,255,0.3);
            margin-bottom: 30px;
        }}
        h1 {{ color: var(--cyan); text-shadow: 0 0 8px var(--cyan); margin: 0; letter-spacing: 4px; }}
        h2 {{ color: var(--mag); border-bottom: 1px solid var(--mag); padding-bottom: 5px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
        .card {{
            background: var(--bg2); border: 1px solid var(--cyan);
            padding: 15px; box-shadow: inset 0 0 8px rgba(0,255,255,0.1);
        }}
        .metric {{ font-size: 2em; color: var(--green); font-weight: bold; text-shadow: 0 0 6px var(--green); }}
        .label {{ color: var(--dim); font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: var(--bg2); color: var(--cyan); padding: 10px; text-align: left; border: 1px solid var(--cyan); }}
        td {{ padding: 8px; border: 1px solid #333; }}
        .warning {{ color: #ffaa00; background: rgba(255,170,0,0.1); padding: 10px; border: 1px solid #ffaa00; }}
    </style>
</head>
<body>
    <header>
        <h1>ASTERION STATISTICS CONSOLE</h1>
        <p>RETRO-FUTURISTIC ANALYTICS • LOCAL REPORT • NO REMOTE DEPENDENCIES</p>
        <p>GENERATED: {timestamp}</p>
    </header>
    
    <h2>DATA COUNTS</h2>
    <div class="grid">
        <div class="card"><div class="metric">{total_events}</div><div class="label">TOTAL TAB EVENTS</div></div>
        <div class="card"><div class="metric">{total_feedback}</div><div class="label">FEEDBACK RECORDS</div></div>
        <div class="card"><div class="metric">{valid_feedback}</div><div class="label">ELIGIBLE TRAINING ROWS</div></div>
        <div class="card"><div class="metric">{test_feedback}</div><div class="label">TEST RECORDS (EXCLUDED)</div></div>
        <div class="card"><div class="metric">{incomplete}</div><div class="label">INCOMPLETE/INVALID</div></div>
    </div>
    
    <h2>DATA QUALITY</h2>
    <table>
        <tr><th>CHECK</th><th>STATUS</th><th>NOTES</th></tr>
        <tr><td>Schema validation</td><td>APPLIED</td><td>Records validated on export</td></tr>
        <tr><td>Test data exclusion</td><td>APPLIED</td><td>is_test flagged and test.example domain excluded</td></tr>
        <tr><td>Historical integrity</td><td>PRESERVED</td><td>No synthetic labels created; incomplete records excluded from training</td></tr>
    </table>
    
    <h2>MODEL EVALUATION</h2>
    {"<div class='warning'>INSUFFICIENT GENUINE DATA FOR TRAINING - Baseline only active. Need 20+ eligible v2 feedback with both labels.</div>" if model_meta is None else f"<table><tr><th>METRIC</th><th>VALUE</th></tr><tr><td>Model Type</td><td>{model_meta.get('model_type')}</td></tr><tr><td>Trained</td><td>{model_meta.get('trained_at')}</td></tr><tr><td>Evaluation Method</td><td>{model_meta.get('metrics',{{}}).get('evaluation_method')}</td></tr><tr><td>Precision</td><td>{model_meta.get('metrics',{{}}).get('precision')}</td></tr><tr><td>Recall</td><td>{model_meta.get('metrics',{{}}).get('recall')}</td></tr><tr><td>F1</td><td>{model_meta.get('metrics',{{}}).get('f1')}</td></tr></table>"}
    
    <footer style="margin-top: 40px; text-align: center; color: var(--dim); border-top: 1px solid var(--cyan); padding-top: 20px;">
        <p>ASTERION LOCAL-FIRST ML TAB PRIORITIZATION • AGGREGATED METRICS ONLY</p>
    </footer>
</body>
</html>"""
    
    with open(HTML_PATH, 'w') as f:
        f.write(html)
    print(f"Wrote {HTML_PATH}")
    
    md = f"""# Asterion ML Evaluation Report

Generated: {timestamp}

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
- Genuine eligible samples: {valid_feedback}

## Evaluation Results
{"Model not trained - insufficient genuine data." if model_meta is None else json.dumps(model_meta.get('metrics'), indent=2)}

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
"""
    with open(MD_PATH, 'w') as f:
        f.write(md)
    print(f"Wrote {MD_PATH}")


if __name__ == "__main__":
    generate()
