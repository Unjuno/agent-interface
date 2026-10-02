# Formal run record

- Allocation: `PHASE-DIVERSIFIED-6067-T0-20261002-01`
- Frozen sources: `candidate.py` and `audit.py`; hashes in `FREEZE.json` / `SHA256SUMS`.
- Commands, run once after freeze from this directory:
  - `python candidate.py`
  - `python audit.py`
- Independent result: schedule count 12,546; all three 12-phase miss vectors match exactly; tests 3/3 pass.
- Candidate invocations: 1. Independent auditor invocations: 1. Formal retries: 0.
- No container, GUI, model, input, network, or application process used for the analytic run.
