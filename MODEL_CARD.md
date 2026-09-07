# AURA-1 Alpha 0.1 — Application Card

## Overview

AURA-1 Alpha 0.1 is an experimental local personal-assistant application
developed by Untoz. This release is an orchestration and interface layer around
the unmodified `Qwen/Qwen3-4B-Instruct-2507` model. It is not yet a separately
trained AURA-1 language model.

## Model and attribution

- Runtime model: Qwen3-4B-Instruct-2507
- Developer: Qwen team, Alibaba Cloud
- Source: https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507
- Upstream license: Apache License 2.0
- Default runtime: Transformers with optional 4-bit quantization

The release archive does not redistribute model weights. Transformers downloads
them from the upstream repository on first use. See `NOTICE` and `LICENSE`.

## AURA application layer

Untoz provides the system prompt, local browser and terminal interfaces,
conversation and structured persistent memory, tool routing, tool validation,
and the read-only local tools included in this repository.

## Intended use

- Local personal assistance
- English-first conversation with Portuguese support
- Writing, explanations and general instruction following
- Safe arithmetic, date/time and system information
- Controlled file-name discovery inside the project

## Evaluation

The application has automated tests covering memory, tools, security boundaries
and the local web API. A local smoke test confirmed end-to-end generation through
the browser server. This is not a comprehensive evaluation of factuality,
bias, instruction following or safety.

## Limitations

Model output may be incorrect, incomplete, outdated or biased. The Alpha is
single-user and localhost-only. It has no public-server authentication,
multi-user isolation or streaming output. It should not be presented as a
replacement for professional advice in high-stakes domains.

## Future model work

The longer-term AURA-1 model project plans a reproducible fine-tune with a
licensed and documented dataset. That future artifact will receive its own
model card, evaluation results and version, separate from this application Alpha.

## Version

Application release: `0.1.0-alpha.1`.
