# AURA-Dataset v0.1

## Purpose

AURA-Dataset v0.1 is the training-data specification and curation layer for AURA-1. Its goal is to improve instruction following, European Portuguese quality, English capability, coding, reasoning, writing, general knowledge, and assistant behaviour.

## Data principles

- Prefer high-quality data over raw volume.
- Track provenance for every record or source group.
- Do not include private, leaked, or personal data without appropriate rights and safeguards.
- Do not redistribute copyrighted material unless its licence permits redistribution and model-training use.
- Prefer synthetic, user-authored, public-domain, or clearly permissive/licensed data.
- Remove secrets, credentials, unnecessary personal information, and unsafe identifying information.
- Deduplicate near-identical examples.
- Keep evaluation data separate from training data.

## Initial categories

1. Portuguese (European Portuguese)
2. English
3. General conversation
4. Instruction following
5. Coding
6. Reasoning
7. Writing and rewriting
8. General knowledge
9. Tool use
10. AURA assistant behaviour

## Record format

Training records use JSONL. Each record follows `data/schema.json` and contains an ID, language, category, conversation messages, provenance, and licence information.

## Versioning

`v0.1` is the first experimental dataset version. The dataset is expected to evolve through curation, validation, deduplication, and evaluation feedback.

## Current status

M002 — dataset foundation and schema. The repository currently contains a small synthetic example set for format validation; it is **not yet a production training dataset**.
