
# Asterion

Asterion is a local-first Chrome extension that ranks browser tabs by usage and helps users decide which tabs to review or close. It uses activity data and user feedback to support tab prioritization.

## Features

- Tracks activity on HTTP and HTTPS tabs.
- Uses a local Python FastAPI backend.
- Stores tab events in MongoDB.
- Ranks domains using available activity signals, including time spent, activations, and recency.
- Accepts useful/not useful feedback.
- Alerts users when the number of relevant open tabs reaches the configured threshold.
- **Tabs to Review:** recommends tabs to review based on available activity data. Users must explicitly choose to close a tab; tabs are never closed automatically.
- Uses a classic Windows 98 / Internet Explorer-inspired interface.

## Requirements

- Python and pip
- Google Chrome
- MongoDB running locally
- Git (optional, for cloning the repository)

## Quick start

### 1. Get the project

Clone the repository and enter the project directory, or open your existing Asterion directory:

```bash
cd ~/Desktop/projects/Asterion
```

### 2. Set up Python

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

If the application requires environment variables, create a `.env` file in the project root. Add the variables used by `config.py`.

For the default local setup, the configuration may look like this:

```dotenv
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=asterion
API_HOST=127.0.0.1
API_PORT=8000
```

Check `config.py` to confirm which variables are required and how they are loaded. Do not commit `.env` files, real credentials, or private configuration.

### 4. Start MongoDB

Start MongoDB locally on port `27017`, unless your configuration specifies another connection address.

### 5. Start the API

With the virtual environment activated, run:

```bash
uvicorn api:app --host 127.0.0.1 --port 8000
```

The API should be available at:

- API: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

### 6. Load the Chrome extension

1. Open `chrome://extensions/`.
2. Enable **Developer mode**.
3. Select **Load unpacked**.
4. Choose the repository's `extension/` directory.

## Usage

- Start the backend and make sure MongoDB is running when required.
- Browse normally. The extension tracks supported HTTP and HTTPS tabs.
- Click the Asterion extension icon to view rankings.
- Submit useful/not useful feedback when available.
- Open **Tabs to Review** to see suggested tabs and the available reasons for each recommendation.
- Click **Close tab** only when you want to close that specific tab. Use **Keep** to dismiss a suggestion when supported.

## Tab-count alert

- Counts relevant HTTP and HTTPS tabs; browser-internal pages are excluded.
- The default threshold is 20 tabs.
- When the threshold is crossed, the extension can show a Chrome notification and a badge.
- A 10-minute cooldown limits repeated alerts while the count remains above the threshold.
- If the count falls below the threshold and later crosses it again, another alert can be triggered.

These details describe the intended behavior. Verify them against the current implementation if the alert configuration changes.

## Tabs to Review

- Uses available activity records and ranking information to suggest tabs for review.
- Excludes the active tab, pinned tabs, internal/browser pages, and other unsupported tabs according to the available Chrome tab state.
- Excludes tabs playing audio when that state is detectable.
- Uses existing ranking information where supported. A lower priority score may indicate a review candidate, but selection and ordering depend on the implementation.
- When activity data is missing, the UI should indicate that there is not enough data rather than inventing evidence.
- Closing requires an explicit user action. The extension should use the selected tab's Chrome tab ID and must not close tabs automatically.
- If the API is unavailable or returns no usable data, recommendations may be limited or unavailable.

## Data and machine learning

- The baseline uses available activity signals such as time spent, activations, and recency.
- Model training and reliable evaluation require enough valid feedback data.
- When the data is insufficient, the baseline remains active.
- Existing feedback is reused where supported. Synthetic training examples are not created to inflate the dataset.
- Model performance should only be reported after an actual evaluation on suitable data.

## Reports

- HTML statistics report: `reports/asterion_statistics.html`
- ML evaluation report: `reports/ASTERION_ML_EVALUATION.md`

Review generated reports for private browsing data before publishing them.

## Tests

Activate the project's virtual environment and run:

```bash
pytest -q
```

Report the actual test results; do not assume all tests pass without running them.

## Privacy and security

- Asterion is designed to run locally, with the API bound to `127.0.0.1` by default.
- Local execution alone does not prove that every component is free of external network requests. Review the code and dependencies before making stronger privacy claims.
- Do not commit `.env` files, credentials, private browsing data, database dumps, or other sensitive files.
- Review feedback datasets and generated reports before publishing them. They must not expose personal browsing history or identifiable user information.

## Limitations

- The FastAPI backend must be started manually. Automatic startup at login is not currently configured.
- MongoDB must be running for features that depend on stored data.
- The ML model requires enough valid feedback before it can be trained and evaluated reliably. Until then, the baseline ranking remains active.
- Tabs to Review depends on the activity data and tab state available to the extension. Recommendations may be limited when data is missing.
- Other users cannot access your local backend through `127.0.0.1:8000`. They must set up the extension, backend, and MongoDB on their own computers unless the architecture is adapted for a suitable shared service.
- The project is intended as a local development and portfolio project. It is not yet a one-click public service or a fully packaged release.

## Future improvements

- Configure optional backend startup at login.
- Simplify installation for other users.
- Collect more valid feedback and evaluate the trained ML model.
- Improve recommendation evaluation and user controls.
- Prepare the extension for wider distribution after testing and security review.
