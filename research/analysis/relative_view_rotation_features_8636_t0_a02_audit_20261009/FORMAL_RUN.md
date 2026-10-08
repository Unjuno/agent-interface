# Formal audit invocation record

- Allocation: `UNJUNO-8636-A02-RAW-AUDIT-A01-20261009`
- Freeze commit: `ecd66d814b7f17f7013a541148d000f3d86cf002`
- Base main: `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`
- Input archive: SHA-256 `a9004e4e84dadcdd6595dd738bec77e69de84e5b51767985129f968649ddeeb9`
- Runtime: CPython 3.12.13, `/run/current-system/sw/bin/python3.12`, macOS 27.0.1 arm64.
- Candidate invocation: 0. A02 candidate was not rerun.
- Audit invocation: 1/1, exit 1, retry 0.
- Start UTC: `2026-10-08T21:04:05Z`; end UTC: `2026-10-08T21:04:06Z`.
- Exact command: `python3.12 -B research/analysis/relative_view_rotation_features_8636_t0_a02_audit_20261009/audit.py --archive research/analysis/relative_view_rotation_features_8636_t0_a02_audit_20261009/inputs/a02-first-outcome.tar.gz --result research/analysis/relative_view_rotation_features_8636_t0_a02_audit_20261009/results/a03-audit.json`
- First output: `ValueError: status mismatch trial=pure_yaw-30030-viewstate_oracle step=3 actual=ACTION expected=STOP fault=None arm=viewstate_oracle`.
- No audit summary was written; the frozen runner stopped at the first discrepancy before source-independent result gates and mutation controls. Exact stdout, stderr, exit, and timestamps are retained under `results/`.

This audit allocation is consumed. Do not rerun or amend its code/results in place. A02 remains `HOLD_UNCERTAIN`.
