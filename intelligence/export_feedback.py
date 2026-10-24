
import csv
import math
from pathlib import Path

from storage.database import feedback_events

FEATURES = [
    "time_score",
    "activation_score",
    "recency_score",
    "weighted_score",
]

COLUMNS = [
    "domain",
    *FEATURES,
    "label",
    "scoring_version",
    "is_test",
    "timestamp",
]

OUTPUT_PATH = Path(__file__).resolve().parent / "feedback_dataset.csv"


def validate_record(record):
    """Return an error message if a feedback record is invalid."""
    if not record.get("domain"):
        return "missing domain"

    if record.get("label") not in {"useful", "not_useful"}:
        return "invalid or missing label"

    for feature in FEATURES:
        value = record.get(feature)

        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return f"missing or non-numeric {feature}"

        if not math.isfinite(value) or not 0 <= value <= 1:
            return f"{feature} must be between 0 and 1"

    if record.get("timestamp") is None:
        return "missing timestamp"

    return None


def export_feedback():
    records = list(feedback_events.find().sort("timestamp", 1))

    valid_rows = []
    invalid_count = 0

    for record in records:
        error = validate_record(record)

        if error:
            invalid_count += 1
            print(f"Skipping record {record.get('_id')}: {error}")
            continue

        valid_rows.append({
            "domain": record["domain"],
            "time_score": record["time_score"],
            "activation_score": record["activation_score"],
            "recency_score": record["recency_score"],
            "weighted_score": record["weighted_score"],
            "label": record["label"],
            "timestamp": record["timestamp"].isoformat(),
            "scoring_version": record.get("scoring_version", "legacy"),
            "is_test": record.get("is_test", False),
        })

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(valid_rows)

    useful = sum(row["label"] == "useful" for row in valid_rows)
    not_useful = sum(row["label"] == "not_useful" for row in valid_rows)

    print("\nAsterion feedback export")
    print("------------------------")
    print(f"Records found:       {len(records)}")
    print(f"Valid records:       {len(valid_rows)}")
    print(f"Skipped records:     {invalid_count}")
    print(f"Useful labels:       {useful}")
    print(f"Not useful labels:   {not_useful}")
    print(f"CSV saved to:        {OUTPUT_PATH}")

    versions = feedback_events.aggregate([
        {
            "$group": {
                "_id": {
                    "$ifNull": ["$scoring_version", "legacy"]
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ])

    print("\nRecords by scoring version:")
    for version in versions:
        print(f"{version['_id']}: {version['count']}")

if __name__ == "__main__":
    export_feedback()
