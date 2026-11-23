# Issue #57 failed-turn UNKNOWN-usage custody R04 - 2026-11-23

## Result

**PASS_SYNTHETIC_FAILED_TURN_UNKNOWN_USAGE_CUSTODY_HOLD.** On current main
d58deb08567325d103eadb7966654907293d10e1, a synthetic JSONL peer returned
terminal status failed and sent no tokenUsage notification. The real client,
planner, grounding model, v3 adapter, caller, durable Calc allocation, and
registered ProspectiveRun custodian preserved one failed attempt with
turn-ledger-1 / thread-ledger-1 identity and usage UNKNOWN. All five usage
totals remained None, never zero. No execution/effect receipt was persisted;
task projection and run finalization remained HOLD, with 17 assignments
missing and dispatch disabled.

Focused 1/1 and the complete eight-test transport/custody module passed in
normal and optimized modes on Windows CPython 3.13.14 with Pillow 12.2.0.
Raw streams and exit codes are preserved. An earlier normal seven-test run
used a stale local origin/main ref at 2cf4230 and omitted the R03 test merged
in d58deb0; it is retained as nonqualifying lineage evidence. The first
assertion expected a null usage_totals container; the observed contract is a
five-field map of null values. The corrected check passed before the frozen
qualifying runs.

## Limits

This was a fake JSONL provider peer with a synthetic allocation verifier and
no GUI, input, live provider, Docker, WSLc, or external custody. It validates
one fail-closed accounting path only. It does not prove provider-side usage
completeness, a live comparison, task success, recovery reliability, runtime
distribution, or Research Preview graduation. Keep Issue #57 open.

See CONDITIONS.json, result.json, raw .bin outputs, and SHA256SUMS.
