# Raw hash non-reconstructibility from RGB PNG

Issue #4106. Exact representation-boundary experiment over the current X11 `CaptureArtifacts.write`.

Read `PLAN.md` and `RESULT.md`. The six-row formal evidence is in `formal-01/RAW.json`; PNG bytes are retained losslessly as hex in each row. `vendor_capture_artifacts.py` is byte-identical to upstream Git blob `d20d67bc06d92d99859681f62fbeb9c2f13aab70`.

The preformal auditor v1 is retained unchanged. A post-formal corruption challenge found that v1 did not validate the recorded byte-order claim; `audit_v2.py` is an explicitly versioned read-only correction and rejects all 10 retained evidence mutations. No formal encoder case was rerun.

This is research evidence only. It does not change runtime behavior or require retaining X11 raw bytes in production.
