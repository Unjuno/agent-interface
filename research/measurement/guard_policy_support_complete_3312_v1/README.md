# #3312 retained evidence

This directory retains the first formal support-complete allocation for Issue #3312. The formal experiment is consumed; do not rerun it under the same allocation ID.

Review `PLAN.md`, `FREEZE.json`, `REPORT.md`, frozen `AUDIT.json`, and postformal `AUDIT_V2.json`. The lossless bundle parts reconstruct the full frozen source, construction record, raw result, process receipts, fixture journal and audits.

Read-only reconstruction:

```sh
python -B unpack.py /tmp/guard3312
cd /tmp/guard3312
python -B audit.py formal/RESULT.json --out /tmp/guard3312-audit.json
python -B audit_v2.py formal/RESULT.json --out /tmp/guard3312-audit-v2.json
```

Expected exits are 0. These commands audit retained bytes only; do not run `run.py` or `construction_live.py` from the restored bundle.
