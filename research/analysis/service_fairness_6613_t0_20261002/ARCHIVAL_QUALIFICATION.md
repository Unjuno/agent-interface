# Archival qualification: pre-run source-hash STOP

This is an immutable recovery copy of the preparation package at original branch tip `24c089a31` (`research/service-fairness-6613-t0-hostcpu-20261002`). It is retained to make the predecessor STOP and its frozen inputs auditable; it is not an experiment result and is not a runnable allocation.

## H / T / D / C / U

- **H:** No hypothesis disposition is available from this allocation. The frozen source identity gate failed before formal execution.
- **T:** The original `FREEZE.json`, README, candidate/auditor sources, fixtures, runners, and construction tests are preserved byte-for-byte. No candidate, formal auditor, retry, or result-output generation was performed during this archival recovery.
- **D:** `STOP_PREREGISTRATION_HASH_MISMATCH`. Of the eight entries in `FREEZE.json.sha256`, seven source hashes reproduce. `candidate.py` does not: frozen expected SHA-256 `4de0d746b2d242b22e8946ffa9318e2f13de298b4db2c6097bbeef982f8882bf`; original branch bytes SHA-256 `774876c0f0b8aca401fc2f65c7a75a0e1618accbf7dcf8338a916d8c6b4e7505`. The original package contains no `candidate_raw.json` or `audit.json`.
- **C:** This records a source/freeze identity inconsistency only. It does not determine which candidate version was intended or establish a policy outcome.
- **U:** No PASS/FAIL hypothesis result, service fairness, human, GUI, authority, safety, or product claim follows. Do not repair this freeze or run it as a retry. The later service-debt A01 and EDF allocations are distinct successors with their own preserved outcomes; do not pool them with this STOP.

The source files other than this qualification are copied unchanged from the original branch. The related Issue #6613 records the predecessor `STOP_PREREGISTRATION_HASH_MISMATCH` and the later distinct allocations.
