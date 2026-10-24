# Asterion

Asterion is a local-first tool to rank browser tabs by use. It tracks tab use, ranks domains, and uses feedback to improve results.

## Features
- Chrome extension tracks HTTP tab use.
- FastAPI backend runs locally.
- MongoDB stores data locally.
- Baseline ranks domains by time, activations, and recency.
- Mark results as useful or not useful.
- Get an alert if you have many open tabs.
- Tabs to Review: suggests which open tabs you may want to close based on real activity data. You must close tabs explicitly. No automatic closing.

## Quick start
1. Make a virtual environment:
```bash
cd ~/Desktop/projects/Asterion
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2. Set environment:
```bash
cp .env.example .env
```
3. Start MongoDB on port 27017.
4. Start the API:
```bash
uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```
5. Load the extension in Chrome:
- Open `chrome://extensions/`
- Turn on Developer mode
- Click "Load unpacked"
- Select `~/Desktop/projects/Asterion/extension/`

## Use
- Browse normally. The extension tracks HTTP tabs.
- Click the Asterion icon to see rankings.
- Give useful or not useful feedback.
- Use "Tabs to Review" to see suggestions based on real activity data. Review reasons and evidence, then click "Close tab" only if you want to close it. Click "Keep" to dismiss. Active tab, pinned tabs, internal/browser pages, and tabs playing audio are excluded by default.
- If you open 20 or more relevant tabs, Asterion shows a notification and a badge.

## Tab alert
- Count: open relevant tabs (http/https). Internal pages like chrome:// are not counted.
- Threshold: 20 tabs (default).
- Alert: Chrome notification. A red badge shows the count.
- Cooldown: 10 minutes. No repeat alert while above threshold in cooldown.
- Reset: if count falls below threshold, you can get an alert again when it crosses up.

## Tabs to Review
- Uses real activity data from stored tab events (time, activations, recency) and existing ranking scores.
- Exclusions: active tab, pinned tabs, tabs playing audio (when detectable), discarded tabs, and internal/browser pages (chrome://, chrome-extension://, edge://, about:, devtools://, etc.).
- Recommendations are ranked by inverse of the baseline ranking score when available. If data is missing, the UI states there is not enough activity data and gives limited reasons.
- Closing requires explicit user action (click "Close tab"). No automatic closing. The exact tab ID is used for closing.
- If the API is offline or returns no data, the feature degrades gracefully.

## Data and ML
- Baseline formula uses time, activations, and recency.
- Training needs enough valid feedback.
- If data is not enough, baseline stays active.
- Feedback from the existing feedback pipeline is reused where possible. No synthetic training samples are created.

## Reports
- HTML: `reports/asterion_statistics.html`
- Markdown: `reports/ASTERION_ML_EVALUATION.md`

## Test
```bash
pytest -q
```

## Privacy
- Runs locally by default.
- The API listens on 127.0.0.1 and is not intended for direct public access.
- No data is intentionally sent to remote sites by the local application.
- Keep secrets in local files. Do not commit `.env` or other secrets.

## Limitations
- The FastAPI backend must be started manually before you use features that depend on it (no automatic startup at login is currently implemented).
- MongoDB must be running for features that depend on stored data.
- Automatic backend startup at login is not currently configured.
- The ML model needs enough valid feedback before it can be trained and evaluated reliably. Until then, the baseline ranking remains active.
- Tabs to Review uses only available activity data. If no data exists for a domain, it states there is not enough activity data.
- Other users cannot use your local backend through `127.0.0.1:8000`. They must set up the extension, backend, and MongoDB on their own computers, or the project must be adapted for a suitable shared service.
- The project is currently intended as a local development and portfolio project. It is not yet a one-click public service or a fully packaged release.

## Future improvements
- Start the backend automatically at login.
- Simplify installation for other users.
- Collect more valid feedback and evaluate the trained ML model.
- Prepare the extension for wider distribution after testing and security review.
