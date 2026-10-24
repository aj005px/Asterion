
# Asterion

Asterion is a local-first, ML-powered Chrome extension that ranks browser tabs based on usage and helps users decide which tabs to review or close. It combines activity tracking, user feedback, and a classic Windows 98-inspired interface.

## Features

- Tracks activity on HTTP and HTTPS tabs.
- Ranks domains using time spent, activations, and recency (weighted baseline preserved).
- **Hybrid ML ranking**: Trained Logistic Regression model (with StandardScaler) uses baseline scores + activity features and learns from genuine Useful/Not useful feedback; predicted probability of usefulness blends with the baseline score for live recommendations.
- Collects useful/not useful feedback (historical supervision only; feedback is never used as inference-time input).
- Alerts users when the number of open tabs reaches a configured threshold.
- Recommends tabs to review, with user-controlled closing (never auto-closes).
- Uses a local FastAPI backend and MongoDB to store tab events.
- Safe fallback to baseline-only ranking if no valid/trained model or insufficient trustworthy data.

## Tech Stack

| Component | Technology |
|---|---|
| Browser extension | JavaScript, Chrome Extension API |
| Backend | Python, FastAPI |
| Database | MongoDB |
| Machine learning | Activity-based ranking and feedback-driven training pipeline |
| Interface | HTML, CSS, JavaScript |

## Setup

### Requirements

- Python and pip
- Google Chrome
- MongoDB
- Git

### 1. Clone the repository

```bash
git clone https://github.com/aj005px/Asterion.git
cd Asterion
```

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Start MongoDB and the backend

Ensure MongoDB is running locally, then start the API:

```bash
MONGO_URI=mongodb://localhost:27017/ uvicorn api:app --host 127.0.0.1 --port 8000
```

API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Load the Chrome extension

1. Open `chrome://extensions/`.
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select the repository's `extension/` directory.

## Results and Evaluation

- **Automated tests:** 16 passed in the latest run (core + tab warning tests).
- **Tab-count alert:** Manually tested and reported to work.
- **Ranking:** Hybrid ML + baseline. Baseline formula preserved (time 40%, activation 35%, recency 25%). When a valid trained model exists with sufficient trustworthy data, ML predicted probability of usefulness influences ranking via blending; otherwise baseline-only ranking is used.
- **Machine learning:** Genuine user feedback trains the Logistic Regression + StandardScaler model (chronological split, validation, no leakage). Feedback is not used at inference time. If insufficient data/invalid/missing model, baseline fallback is automatic and safe.

Detailed reports:

- [HTML Statistics Report](reports/asterion_statistics.html)
- [ML Evaluation Report](reports/ASTERION_ML_EVALUATION.md)

## Limitations

- MongoDB and the backend require local setup.
- The backend must be started manually.
- Recommendations depend on available activity data.
- Reliable model training requires sufficient valid feedback.
- The project is a local development prototype, not a packaged public service.
