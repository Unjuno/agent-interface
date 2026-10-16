# Invocation-boundary audit successor T1

This additive evidence package repairs the no-op positive-row mutation check from T0 and re-audits the unchanged T0 raw JSONL.

- `FREEZE.json` — hypothesis, gates, predecessor identity, source/input hashes, and invocation budget.
- `audit.py` — independent raw-only oracle; it does not import a candidate runner.
- `inputs.json`, `results/raw.jsonl` — frozen finite fixture and byte-identical predecessor raw.
- `test_audit_mutation.py` — construction regression test for the changed positive-row mutation.
- `results/AUDIT.json` — the single formal audit result.
- `RESULT.md` — H/T/D/C/U interpretation and exact scope limits.

From this directory, reproduce the finite audit with:

```powershell
python -B audit.py inputs.json results/raw.jsonl results/AUDIT.json
```

The formal decision applies only to this audit-control correction. It does not upgrade the predecessor's allocation or STOP disposition and is not evidence about live X11 key-up timing, physical input occupancy, Docker capacity, or Issue #59 threat response.
