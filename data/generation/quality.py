"""Quality checks and exact/near-duplicate detection for AURA dataset records."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

MIN_USER_CHARS = 8
MIN_ASSISTANT_CHARS = 10
MAX_ASSISTANT_CHARS = 12000


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def quality_issues(record: dict) -> list[str]:
    issues: list[str] = []
    messages = record.get("messages", [])
    user_messages = [m["content"] for m in messages if m.get("role") == "user"]
    assistant_messages = [m["content"] for m in messages if m.get("role") == "assistant"]

    if not user_messages:
        issues.append("missing user message")
    if not assistant_messages:
        issues.append("missing assistant message")

    for content in user_messages:
        if len(content.strip()) < MIN_USER_CHARS:
            issues.append("user message is too short")
    for content in assistant_messages:
        length = len(content.strip())
        if length < MIN_ASSISTANT_CHARS:
            issues.append("assistant response is too short")
        if length > MAX_ASSISTANT_CHARS:
            issues.append("assistant response is too long")

    combined = " ".join(m.get("content", "") for m in messages)
    if "<|endoftext|>" in combined or "<|im_end|>" in combined:
        issues.append("contains model control tokens")

    return sorted(set(issues))


def record_text(record: dict) -> str:
    return " ".join(normalize_text(m.get("content", "")) for m in record.get("messages", []))


def duplicate_pairs(records: list[dict], threshold: float = 0.92) -> list[tuple[str, str, float]]:
    """Return pairs whose normalized conversation text is very similar."""
    pairs: list[tuple[str, str, float]] = []
    normalized = [(r.get("id", ""), record_text(r)) for r in records]
    for i, (id_a, text_a) in enumerate(normalized):
        for id_b, text_b in normalized[i + 1 :]:
            if not text_a or not text_b:
                continue
            score = SequenceMatcher(None, text_a, text_b).ratio()
            if score >= threshold:
                pairs.append((id_a, id_b, round(score, 4)))
    return pairs
