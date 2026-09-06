"""Validate AURA JSONL records against the project's dataset rules."""

from __future__ import annotations

import json
import sys
from pathlib import Path

VALID_LANGUAGES = {"pt-PT", "en", "multilingual"}
VALID_ROLES = {"system", "user", "assistant"}
REQUIRED_FIELDS = {"id", "language", "category", "messages", "source", "license"}


def validate_record(record: dict, line_number: int, seen_ids: set[str]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_FIELDS - record.keys()
    if missing:
        errors.append(f"line {line_number}: missing fields: {', '.join(sorted(missing))}")

    record_id = record.get("id")
    if not isinstance(record_id, str) or not record_id.strip():
        errors.append(f"line {line_number}: id must be a non-empty string")
    elif record_id in seen_ids:
        errors.append(f"line {line_number}: duplicate id: {record_id}")
    else:
        seen_ids.add(record_id)

    if record.get("language") not in VALID_LANGUAGES:
        errors.append(f"line {line_number}: invalid language")

    messages = record.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        errors.append(f"line {line_number}: messages must contain at least two messages")
    else:
        for message_index, message in enumerate(messages, start=1):
            if not isinstance(message, dict):
                errors.append(f"line {line_number}: message {message_index} is not an object")
                continue
            if message.get("role") not in VALID_ROLES:
                errors.append(f"line {line_number}: message {message_index} has invalid role")
            if not isinstance(message.get("content"), str) or not message["content"].strip():
                errors.append(f"line {line_number}: message {message_index} has empty content")

    if not isinstance(record.get("source"), str) or not record["source"].strip():
        errors.append(f"line {line_number}: source must be present")
    if not isinstance(record.get("license"), str) or not record["license"].strip():
        errors.append(f"line {line_number}: license must be present")

    return errors


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                errors.append(f"line {line_number}: empty line")
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
                continue
            if not isinstance(record, dict):
                errors.append(f"line {line_number}: record must be a JSON object")
                continue
            errors.extend(validate_record(record, line_number, seen_ids))
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate.py <dataset.jsonl>")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 2

    errors = validate_file(path)
    if errors:
        print(f"Validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validation passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
