# AURA-1 Roadmap

## M001 — Project Initialization

- [x] Repository created
- [x] Core directory structure created
- [x] Initial documentation created
- [x] Training/evaluation/inference placeholders created

## M002 — AURA-Dataset v0.1

- [x] Define dataset schema
- [x] Establish provenance and licensing metadata
- [x] Build deterministic generation/validation pipeline
- [x] Add quality checks and deduplication
- [x] Curate first Portuguese and English corpus
- [x] Add coding, reasoning, writing, knowledge, tool-use and AURA-behaviour examples
- [x] Publish dataset documentation
- [ ] Expand corpus with reviewed external datasets and/or substantially more original examples
- [ ] Final dataset validation and train/eval split

## M003 — First QLoRA Training

- [x] Profile dataset
- [x] Finalize training configuration
- [ ] Run first experiment
- [ ] Record metrics and hardware
- [ ] Save adapter/checkpoint artifacts

## M004 — AURA-1-v0.1

- [ ] Merge/export model as appropriate
- [ ] Validate inference
- [ ] Produce model card
- [ ] Version the release

## M005 — Evaluation

- [ ] Build benchmark suite
- [ ] Test Portuguese
- [ ] Test English
- [ ] Test coding
- [ ] Test reasoning
- [ ] Test instruction following

## M006 — Ollama

- [ ] Convert/export to supported format
- [ ] Create final Modelfile
- [ ] Test local inference

## M007 — AURA Integration

- [x] Connect AURA-1 to the AURA application
- [x] Add conversation and persistent memory
- [x] Add safe tool system (calculator, date/time, system info and files)
- [x] Add localhost browser prototype
- [x] Add automated integration and web API tests
- [ ] Complete conversational quality benchmark
- [ ] Test latency and resource use
- [ ] Add streamed responses and restored visual history

## M008 — Hugging Face

- [ ] Prepare model repository
- [ ] Publish documentation
- [ ] Publish weights when ready

## M009 — Open-source Release

- [ ] Finalize licenses
- [ ] Verify dataset provenance
- [ ] Publish reproducible instructions
- [ ] Announce AURA-1 release
