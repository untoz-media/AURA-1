# AURA Dataset Generation Pipeline

The generation pipeline creates candidate training examples for AURA-Dataset v0.1.

## Goals

- Generate diverse instruction/response examples.
- Keep European Portuguese as a first-class target.
- Separate generation from validation and final curation.
- Record provenance and licence metadata.
- Never treat generated examples as automatically correct: all generated data must pass validation and, where appropriate, human review.

## Categories

`portuguese`, `english`, `general`, `instruction_following`, `coding`, `reasoning`, `writing`, `knowledge`, `tool_use`, `aura_behavior`

## Usage

The first implementation is intentionally dependency-light and generates deterministic seed examples locally. Future versions can connect to an approved model/API for larger-scale synthetic generation.

```bash
python data/generation/generate.py --count 20 --output data/processed/aura_dataset_generated.jsonl
python data/generation/validate.py data/processed/aura_dataset_generated.jsonl
```

Generated data is candidate data, not automatically release-ready training data.
