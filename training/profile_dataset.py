"""Profile the AURA-1 training dataset before an experiment."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile an AURA-1 JSONL dataset.")
    parser.add_argument(
        "path",
        nargs="?",
        default="data/processed/aura_dataset_v0.1.jsonl",
    )
    args = parser.parse_args()

    path = Path(args.path)
    records = []
    errors = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: {exc}")

    ids = [record.get("id") for record in records]
    languages = Counter(record.get("language") for record in records)
    categories = Counter(record.get("category") for record in records)
    licenses = Counter(record.get("license") for record in records)
    role_counts = Counter(
        message.get("role")
        for record in records
        for message in record.get("messages", [])
    )

    print(f"Dataset: {path}")
    print(f"Examples: {len(records)}")
    print(f"Languages: {dict(languages)}")
    print(f"Categories: {dict(categories)}")
    print(f"Licenses: {dict(licenses)}")
    print(f"Message roles: {dict(role_counts)}")
    print(f"Unique IDs: {len(set(ids))} / {len(ids)}")
    print(f"Malformed lines: {len(errors)}")

    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")

    invalid = []
    for record in records:
        messages = record.get("messages")
        if not isinstance(messages, list) or not messages:
            invalid.append(record.get("id", "<missing id>"))
            continue
        roles = [message.get("role") for message in messages]
        if roles[-1] != "assistant" or roles[0] != "user":
            invalid.append(record.get("id", "<missing id>"))

    print(f"Structural issues: {len(invalid)}")
    if invalid:
        print("  " + ", ".join(invalid))


if __name__ == "__main__":
    main()
