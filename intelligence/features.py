
from collections import defaultdict
from datetime import datetime, timezone

from storage.database import tab_events


def get_domain_features():
    """
    Aggregate tab activity by domain.

    Supports:
    - activate / activated events
    - duration events with duration_seconds
    - deactivated events paired by session_id and tab_id
    """

    events = list(
        tab_events.find(
            {},
            {
                "_id": 0,
                "domain": 1,
                "event_type": 1,
                "timestamp": 1,
                "duration_seconds": 1,
                "session_id": 1,
                "tab_id": 1,
            },
        ).sort("timestamp", 1)
    )

    domains = defaultdict(
        lambda: {
            "total_time_seconds": 0.0,
            "activation_count": 0,
            "last_active": None,
        }
    )

    active_tabs = {}

    for event in events:
        domain = event.get("domain")
        event_type = event.get("event_type")
        timestamp = event.get("timestamp")

        if not domain or timestamp is None:
            continue

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        data = domains[domain]

        if data["last_active"] is None or timestamp > data["last_active"]:
            data["last_active"] = timestamp

        if event_type in {"activate", "activated"}:
            data["activation_count"] += 1

            key = (event.get("session_id"), event.get("tab_id"))

            if all(value is not None for value in key):
                active_tabs[key] = (domain, timestamp)

        elif event_type == "duration":
            duration = event.get("duration_seconds", 0)
            if isinstance(duration, (int, float)) and duration > 0:
                data["total_time_seconds"] += duration

        elif event_type == "deactivated":
            key = (event.get("session_id"), event.get("tab_id"))
            active = active_tabs.pop(key, None)

            if active is None:
                continue

            active_domain, start_time = active
            elapsed = (timestamp - start_time).total_seconds()

            if elapsed > 0:
                domains[active_domain]["total_time_seconds"] += elapsed

    now = datetime.now(timezone.utc)
    features = []

    for domain, data in domains.items():
        last_active = data["last_active"]

        features.append({
            "domain": domain,
            "total_time_seconds": round(data["total_time_seconds"], 2),
            "activation_count": data["activation_count"],
            "recency_seconds": (
                round((now - last_active).total_seconds(), 2)
                if last_active is not None
                else None
            ),
        })

    return features
