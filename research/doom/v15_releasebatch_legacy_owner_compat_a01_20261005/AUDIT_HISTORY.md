# Readback correction history

The first readback implementation reached its report-writing line and stopped with `KeyError: 'scope'` because the collector's compact raw `result.json` did not repeat the scope field. This is an auditor defect, not a candidate or owner-protocol outcome. The first traceback and exit code are retained in `audit-v1.stderr.txt` and `audit-v1.exit.txt`. The corrected `audit.py` sources scope from the frozen package-level `RESULT.json` and verifies the compact run result independently. No compatibility probe was rerun for this correction.
