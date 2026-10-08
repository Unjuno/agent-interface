# Issue #5805 — exploratory finite joint-authority T0

This package preserves a one-shot local synthetic admission experiment. It is **not** a formally allocated repository experiment, real consent study, effect test, or product-safety result. The Idea issue's allocation remains unchanged. No candidate was rerun to publish this evidence.

Read in this order:

1. `PLAN.md` — H/T/D/C/U and scope.
2. `FREEZE.json`, `PREEXEC.json` — frozen source identities and pre-execution gates.
3. `REPORT.md` — result and limitations.
4. `fixtures.py`, `candidate.py`, `run_candidate.py` — authored finite inputs and candidate.
5. `results/run-01/RAW.jsonl`, `results/run-01/AUDIT.json`, `audit.py` — retained raw decisions and the separate literal-table auditor.
6. `test_t0.py`, `test_audit.py` — pre-execution construction and audit mutation checks.

The candidate and auditor ran once each on CPython 3.12.10 / Windows 11, separately, with the Python standard library only. Docker Desktop's `desktop-linux` context did not answer the bounded `docker info` probe; no container was run. There were no real owners, resources, consent messages, GUI interactions, OS input, or effect receipts.

To rerun only the deterministic construction suite from this directory:

```powershell
python -B -m unittest -v
```

Do not interpret a test rerun as a new formal allocation. See `REPORT.md` for exact one-shot commands and SHA-256 identities.
