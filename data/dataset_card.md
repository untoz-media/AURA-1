# AURA-Dataset v0.1

## Purpose

AURA-Dataset v0.1 is the training-data specification and curation layer for AURA-1. Its goal is to improve instruction following, European Portuguese quality, English capability, coding, reasoning, writing, general knowledge, and assistant behaviour.

## Data principles

- Prefer high-quality data over raw volume.
- Track provenance for every record or source group.
- Do not include private, leaked, or personal data without appropriate rights and safeguards.
- Do not redistribute copyrighted material unless its licence permits redistribution and model-training use.
- Prefer original curated examples, public-domain material, or clearly permissive/licensed data.
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

## v0.1 curated corpus

The first committed corpus is `data/processed/aura_dataset_v0.1.jsonl`. It contains 30 original, manually curated examples covering Portuguese (PT-PT), English, instruction following, coding, reasoning, writing, knowledge, tool use, and AURA behaviour.

These examples are deliberately small and high-quality rather than artificially inflated with repetitive generated samples. They establish the first training corpus and the curation standard for later expansion.

## Provenance and licensing

The current corpus uses the `aura-curated` source and `CC0-1.0` because the examples were authored specifically for this project. External datasets will only be added after their licence, redistribution rights, training suitability, and provenance have been reviewed and recorded in `data/metadata/`.

## Versioning

`v0.1` is the first experimental dataset version. The dataset is expected to evolve through curation, validation, deduplication, and evaluation feedback.

## Current status

**M002.5 — Dataset real: complete for the first curated corpus.** The repository now contains an actual 30-record training corpus rather than only generator templates. This is still far too small for serious fine-tuning, so the next iterations will expand coverage and diversity before training AURA-1.
