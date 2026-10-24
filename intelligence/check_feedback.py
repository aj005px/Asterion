import pandas as pd
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent / "feedback_dataset.csv"

FEATURE_COLUMNS = [
    "time_score",
    "activation_score",
    "recency_score",
]

CURRENT_VERSION = "v2"
TEST_DOMAINS = {"test.example"}


def main():
    if not CSV_PATH.exists():
        print("Dataset not found. Run the export script first.")
        return

    df = pd.read_csv(CSV_PATH)

    print("\nAsterion Dataset Quality")
    print("------------------------")
    print(f"Total exported rows: {len(df)}")

    print("\nRecords by scoring version:")
    if "scoring_version" in df.columns:
        print(df["scoring_version"].fillna("legacy").value_counts().to_string())
    else:
        print("Missing scoring_version column. Re-run the export script.")
        return

    print("\nHistorical label balance:")
    print(df["label"].value_counts().to_string())

    # Keep only current-version, non-test examples for readiness checks.
    current = df[
        (df["scoring_version"] == CURRENT_VERSION)
        & (~df["domain"].isin(TEST_DOMAINS))
        & (~df["is_test"].fillna(False).astype(bool))
    ].copy()

    print(f"\n{CURRENT_VERSION} training-candidate rows: {len(current)}")
    print("Excluded test domains:", ", ".join(sorted(TEST_DOMAINS)))

    if current.empty:
        print("\nTraining readiness:")
        print("Not ready: no genuine v2 feedback examples yet.")
        return

    print("\nv2 label balance:")
    print(current["label"].value_counts().to_string())

    print("\nv2 feedback by domain:")
    print(current.groupby("domain")["label"].count().to_string())

    zero_rows = (current[FEATURE_COLUMNS] == 0).all(axis=1)
    print(f"\nv2 rows with all-zero features: {zero_rows.sum()}")

    print("\nTraining readiness:")
    if len(current) < 30 or current["label"].nunique() < 2:
        print(
            "Not ready: collect more genuine v2 feedback "
            "with both useful and not_useful labels."
        )
    else:
        print(
            "Enough rows for an initial experiment, "
            "but model quality still needs proper evaluation."
        )


if __name__ == "__main__":
    main()
