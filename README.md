
# Asterion

Asterion is a local-first, ML-powered Chrome extension that ranks browser tabs based on usage and helps users decide which tabs to review or close. It combines activity tracking, user feedback, and a classic Windows 98-inspired interface.

## Features

- Tracks activity on HTTP and HTTPS tabs.
- Ranks domains using time spent, activations, and recency.
- Collects useful/not useful feedback.
- Alerts users when the number of open tabs reaches a configured threshold.
- Recommends tabs to review, with user-controlled closing.
- Uses a local FastAPI backend and MongoDB for storing tab events.

## Tech Stack

| Component | Technology |
|---|---|
| Browser extension | JavaScript, Chrome Extension API |
| Backend | Python, FastAPI |
| Database | MongoDB |
| Machine learning | Activity-based ranking, feedback-driven training pipeline |
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

### 3. Configure the environment

Create a `.env` file in the project root if required by `config.py`:

```dotenv
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=asterion
API_HOST=127.0.0.1
API_PORT=8000
```

### 4. Start MongoDB and the backend

Ensure MongoDB is running, then start the API:

```bash
uvicorn api:app --host 127.0.0.1 --port 8000
```

API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 5. Load the extension

1. Open `chrome://extensions/`.
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select the repository's `extension/` directory.

## Results and Evaluation

- **Automated tests:** 9 passed.
- **Tab-count alert:** Manually tested; the alert was reported to work.
- **Ranking:** Uses activity signals including time spent, activations, and recency.
- **Machine learning:** The baseline ranking remains active when feedback is insufficient for reliable model training.

Detailed reports:

- [HTML Statistics Report](reports/asterion_statistics.html)
- [ML Evaluation Report](reports/ASTERION_ML_EVALUATION.md)

The test count reflects the last reported test run and should be updated when tests change. Model performance metrics should only be added after a valid evaluation.

## Limitations

- The backend and MongoDB require local setup.
- The backend must be started manually.
- Recommendations depend on available activity data.
- The project is a local development prototype, not a packaged public service.
