# Safety X-server stall recovery evidence

Issue: #4167. Read `REPORT.md`, `src/PLAN.md`, and `src/FREEZE.json` first.

The formal allocation is consumed. Do **not** rerun it as review. Review is read-only:

```sh
python -B src/audit.py formal/f01/result.json formal/f02/result.json formal/f03/result.json formal/f04/result.json formal/f05/result.json formal/f06/result.json
PYTHONPATH=src python -B src/test_audit.py formal/f01/result.json formal/f02/result.json
```

The full archive contains formal raw files and excluded construction failures. SHA-256 commitments are in `EVIDENCE.json` and inside the archive `SHA256SUMS`.
