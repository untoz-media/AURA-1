"""Run quality checks and remove exact duplicates from a JSONL dataset.

Near-duplicate pairs are reported for review rather than automatically removed.
This conservative behaviour helps avoid deleting useful, legitimately different
training examples.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from quality import duplicate_pairs, quality_issues


def load_records(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"Skipping invalid JSON at line {line_number}: {exc.msg}")
    return records


def exact_key(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Curate an AURA JSONL dataset.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    records = load_records(args.input)
    accepted: list[dict] = []
    seen: set[str] = set()
    rejected = 0

    for record in records:
        issues = quality_issues(record)
        if issues:
            rejected += 1
            print(f"REJECT {record.get('id', '<unknown>')}: {', '.join(issues)}")
            continue
        key = exact_key(record)
        if key in seen:
            rejected += 1
            print(f"REJECT {record.get('id', '<unknown>')}: exact duplicate")
            continue
        seen.add(key)
        accepted.append(record)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for record in accepted:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    pairs = duplicate_pairs(accepted)
    print(f"Input records: {len(records)}")
    print(f"Accepted records: {len(accepted)}")
    print(f"Rejected records: {rejected}")
    print(f"Near-duplicate pairs for review: {len(pairs)}")
    for first, second, score in pairs[:20]:
        print(f"REVIEW {first} <-> {second}: similarity={score}")
    print(f"Curated dataset: {args.output}")


if __name__ == "__main__":
    main()
