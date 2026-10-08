# Raw evaluation-artifact bypass — Issue #8581 T0 A02

This corrected-auditor successor preserves a second first outcome without rewriting A01.

- Freeze: `FREEZE.json`, source commit `fc33cb8cb227c98ed9915d3b486c4c8542a9375e`.
- Candidate: one invocation, exit 0, four cells and 92 events.
- Auditor: one invocation, exit 1 after writing a `HOLD_ACCESS_OR_AUDIT` result with eight replay mismatches and 5/5 mutation rejections.
- Diagnosis: candidate/auditor random-label generation differs; a separate final logging `NameError` also occurred.
- No retries or scientific contrast. See `REPORT.md`, `RUN_LOG.md`, `EXECUTION_RECORD.json`, and `SHA256SUMS.txt`.
