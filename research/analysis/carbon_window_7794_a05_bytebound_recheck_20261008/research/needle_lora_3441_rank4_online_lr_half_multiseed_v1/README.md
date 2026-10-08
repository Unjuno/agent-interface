# Issue #3826 — fixed half-LR rank-4 online LoRA successor

Local RTX 3080 five-seed fresh allocation. H/T/D/C/U and gates are frozen in Issue #3826.

- `runner.py`: one formal invocation, 16 held-out prediction curves at every feedback count for each online arm; lossless gzip/base64 stdout envelope.
- `audit.py`: independently regenerates CPU seed/label streams and audits every final/curve prediction without importing runner.
- `test_construction.py`: construction-only checks; no optimizer update or formal held-out evaluation.
- `FREEZE.json`: exact source hashes and pre-allocation environment.
- Raw result, audit, report and hashes will be added after the single invocation.

Host CUDA only; no Docker/container claim, provider, GUI, task effect or runtime authority.
