# Owner-queue raw-output integrity counterexample (A02)

## H / T / D / C / U

- **H:** the merged #7404 auditor accepts contradictory raw runner text because it checks for passing substrings without validating `SHA256SUMS.txt`; an independent manifest verification detects the altered bytes.
- **T:** copy the exact merged evidence package to temporary directories, run its original auditor on an untouched copy, then append an explicit failure line to `results/RAW_COMPOSITION.txt`. Compare the original auditor result with SHA-256 manifest verification.
- **D:** untouched manifest and original auditor pass; the mutated manifest check fails; the original auditor is expected to continue passing, demonstrating the counterexample.
- **C:** this tests stored-output integrity only. It does not rerun the owner loop or verify correspondence between stdout and structured observations.
- **U:** fake-Xlib saved evidence only; no physical release, live input, useful-feedback/recovery, or MAP01 outcome.

## Result

The original auditor returned 0 and `PASS_OWNER_QUEUE_COMPOSITION` even after contradictory failure text was appended. SHA-256 manifest verification found the altered `RAW_COMPOSITION.txt`. The baseline manifest passed before and after the original audit. Raw summary and machine-readable outcome are retained here.

Run `python -B research/doom/results/map01-v39-owner-queue-raw-integrity-a02-20261004/mutation_test.py` from the repository root.
