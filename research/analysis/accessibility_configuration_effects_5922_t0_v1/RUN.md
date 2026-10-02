# Formal run ledger

- Source freeze commit: `5cd7cce871a99e1b1e52dc6356f7f1fe1be8cc09` (main parent `ee0bf5670c4f9cec0c1de1a0e966eb3dd6566c15`).
- Frozen source identities were checked by downloading each Git blob through the GitHub API and comparing local SHA-256.
- Candidate invocation #1: `python candidate.py`; exit 0; exact stdout was not retained at invocation time.
- Auditor invocation #1: `python auditor.py`; exit 1 before evaluation because `candidate_output.json` was missing. Preserved as failed.
- Recovery mistake: candidate invocation #2 occurred. Output retained as `candidate_output_invalidated.json`; do not treat as formal result. No auditor rerun.
- Current formal disposition: `HOLD_FORMAL_RUN_INVALIDATED`; 0 valid audited candidate results.
- Construction suite: `python -m unittest -v test_construction.py`; 7/7 passed. This is pre/formal construction evidence only.
- Runtime: local host Windows / Python 3.12; no container, browser, GUI, network-in-experiment, model, GPU or external input.
- Stop rule: no more runs under Issue #5922. Any continuation requires a new allocation and direct stdout tee on first candidate invocation.