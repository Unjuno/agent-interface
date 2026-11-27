# Issue #57 provider success-to-custody bridge R03 - 2026-11-23

## Result

**PASS_SYNTHETIC_SUCCESS_USAGE_DURABLE_PROSPECTIVE_JOIN.** Against current
main 2cf4230f918f1b05990a4491779805cc18658e12, one synthetic valid JSONL App
Server turn passed through the real client/parser, persistent grounding model,
v3 adapter, adaptive caller, run_g10_in_durable_allocation, and a registered
ProspectiveRun task custodian. The exact turn-ledger-1 / thread-ledger-1
identity and five usage counters (1,234 input, 234 cached input, 0 cache-write,
56 output, 12 reasoning output) remained one completed attempt and were present
in durable custody audit. Synthetic task/effect receipts were audited and one
task projected.

The focused test passed 1/1 and the full transport/custody module passed 7/7,
both in normal and optimized modes on Windows CPython 3.13.14 with Pillow
12.2.0. Raw stdout, stderr, exit codes, and machine-readable summaries are
preserved in this packet. Two early optimized-harness argument errors are also
preserved and excluded; corrected interpreter-level -O invocations passed.

## Limits

The peer and allocation are synthetic; compiled execution and score evidence
are fixtures. No live provider, GUI, native input, external allocation, Docker,
or WSLc was used. Finalization correctly remained HOLD with 17 of 18
assignments missing and dispatch_enabled: false. This closes one offline
success-transport seam only. Provider completeness, a fully observed three-arm
run, current-source integrated efficiency, recovered caller task
success/reliability, MAP01, distributable-runtime acceptance, and Research
Preview graduation remain open. Keep Issue #57 open.

See CONDITIONS.json, result.json, raw *.stdout.bin / *.stderr.bin files, and
SHA256SUMS. R01 retains the failure/usage counterpart; R02 retains
incomplete-envelope fail-closed behavior.
