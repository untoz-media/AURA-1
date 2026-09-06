# AURA Dataset Quality Policy

## Automatic rejection

A candidate record is rejected when it has missing user/assistant content, extremely short content, an excessively long assistant response, or model control tokens that should not appear in training text.

## Exact duplicates

Exact duplicate records are removed automatically during curation.

## Near duplicates

Near duplicates are detected using normalized text similarity. They are **reported for review**, not automatically deleted. This prevents the pipeline from accidentally removing distinct examples that happen to share wording.

## Human review

Before a dataset version becomes a training release, reviewers should check correctness, usefulness, language quality, instruction adherence, and provenance/licensing.

## Safety and privacy

Do not intentionally include passwords, API keys, private conversations, unnecessary personal information, or other restricted material. Synthetic data is preferred where it can provide the desired behaviour without introducing these risks.

## Release gate

A dataset should only move from candidate data to `AURA-Dataset-v0.1` after validation, deduplication, quality review, and provenance/licence checks have passed.
