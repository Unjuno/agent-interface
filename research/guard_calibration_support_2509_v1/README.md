# Guard calibration support preflight (#2509)

Construction-only preflight for the successor to #1793. It checks that a
prospective ledger schema can represent the required stale/fresh, recovery,
success, and right-censored strata without pooling historical rows.

This is not a formal route allocation and contains no GUI, model, network,
authority, or task input. The fixture rows are explicitly synthetic readiness
controls; they cannot establish the #2509 acceptance criteria.

Run:

```bash
python audit.py
```

Expected disposition: `HOLD_SYNTHETIC_READINESS_ONLY`.
