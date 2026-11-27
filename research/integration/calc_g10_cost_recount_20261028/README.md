# Read-only G10 cost recount (2026-10-28)

This derived recount pins and reads the archived G10 `raw.json`, `OCR_ATTEMPTS.jsonl`, `HOST_RECEIPT.json`, `AUDIT.json`, and `REPORT.md` against the parent `FILES.json` manifest. It does not run the old actor, OCR, container, or auditor and does not change those historical records. Run `python recount.py` to verify the five source hashes and regenerate `recount.json`.

## Reconstructed measurements

- One recorded WSLc construction run: host launcher elapsed **29.933 s**; container process elapsed **26.556 s**. These use different recorded boundaries and must not be subtracted to infer unaccounted work.
- Compiled graph elapsed **1.972 s**, with three graph observations.
- Two native programs: **0.569 s** and **0.566 s**, with one recorded verified-empty release each. These are nested execution intervals and are not additive to graph time.
- Seven Tesseract subprocess attempts, including the retained initial blank output; total subprocess interval **0.494 s**. The first-start-to-last-end span is **1.906 s** and includes gaps between attempts.
- The original audit reports two saved effects passing. The timestamp for the independent saved-file scoring is not joined to the host run, so elapsed time to independently scored task effect is unavailable.

## Missing comparison data

The original report and audit say primary model usage is **UNKNOWN**, with zero additional benchmark model calls. Actual primary model attempts, token usage, model wait, images shown to the model, and end-to-end task time to independent scoring are not recoverable from this run. Cold/warm/invalidation/repair phases, a matched baseline, speedup, and reuse break-even were not measured. Do not derive an efficiency percentage from these numbers.

The G10 result remains one scoped positive fixed-layout/font Calc construction with OCR and separate saved-effect scoring. Requested WSLc resource settings are not proof of enforcement. This recount adds no new live, model, Docker, or GUI evidence.
