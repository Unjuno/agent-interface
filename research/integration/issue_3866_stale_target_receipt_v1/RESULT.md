# Issue #3866 formal01 result

Date: 2026-09-21 (Asia/Tokyo)
Source main: `688e45cb99af4af7cc71db77049b5a6135a2f36f`
Decision: `PASS_STALE_TARGET_BLOCKED_SCOPED`
Formal allocation: 6 sessions, one run, zero reruns; fixed schedule A1,B1,B2,A2,A3,B3.

## Question and scope
On a private LibreOffice Calc fixture, can a guard requiring an app-owned UNO selection receipt for `$Sheet1.$A$1` plus matching active Calc window identity prevent keyboard entry when the historical fixed point `[89,200]` actually selects `$Sheet1.$A$3`? This synthetic GUI result does not explain Issue #2704's earlier `FAIL_EFFECT_MISMATCH` and makes no production CLI/native exchange claim.

## Outcome
All three coordinate-only A controls emitted the fixed task sequence and independently scored A3=116, A4=476, while A1/A2 remained blank. In each B arm the UNO receipt observed A3, the guard refused before task keyboard input, the workbook remained blank, and independent XRecord reported zero key events (one pointer click pair). Thus this narrowly scoped guard blocked the reproducible stale-target write in all three paired trials.

The standalone auditor ran in a separate Docker invocation and returned `PASS_STALE_TARGET_BLOCKED_SCOPED`, six sessions, zero integrity/event/hash errors. It independently read workbook values, event traces, row/workbook hashes, focus/window/profile identity, process cleanup, and disposition.

## Container and provenance
Docker Desktop Server 28.5.1, linux/amd64. Image `issue2704-calc-readiness:formal01`, ID `sha256:41c3190256bf644c8e251bb84d615d2753fae067e347422fd6d3e74ec8d60183`; base image digest `c0d1b4471b2095cec5aee92d31a46e35a96a20b6cf469443c307e9670b493544`. Formal run used `--pull=never --network none --read-only`, disposable evidence mount and bounded tmpfs. Runtime package versions and exact source hashes were preregistered in Issue #3866 before the formal allocation.

Source bundle hashes (SHA-256):
- `audit.py`: `EB8473E7E72A8AFA63D1930E2C791828A6205F79FF069969FEEC90EAB122EEA9`
- `construction_xrecord_probe.py`: `16664AB6DD39734A20A3D5F2658B963F46F084024C650B4272574DF9B4C131E1`
- `Dockerfile`: `273F1CFA433DF640C57DEA85697DE3272034114F579030B0F9ED3AB4C0CD7810`
- `README.md`: `0C3499F22E2B1BFD93833914F4DF3598D819F6AEDC9580BED70070E38FD71EAD`
- `record_monitor.py`: `5A9A25F6FF5B7BCB37E36C62800CF0661D56245293B60973FA1DC9FC971870D3`
- `runner.py`: `8694A7BE79B12EC6DAFC1CA851D40E8286620B43692A7AF28635E49DE1726C0C`

## Construction/stops
An initial Docker image build using a digest-qualified local FROM was blocked by Docker Hub access (`insufficient_scope`); it was corrected to use the already cached immutable base tag and built successfully. Initial XRecord collector construction blocked synchronously; after implementing a threaded collector, a separate calibration captured key press/release and exited 0. A process-cleanup construction run exposed lingering LibreOffice processes; cleanup was bounded and escalates TERM to KILL, then a fresh construction-only run confirmed no remaining profile processes and all fixture children reaped. These were construction iterations only; no formal sessions were consumed by them.

## Integration
Evidence output and independent audit JSON are retained with the research worktree. This report is the GitHub-facing durable result. Keep Issue #2704's earlier failure unchanged; Issue #3866 records this successor experiment. Any production integration should be a separate change with its own end-to-end acceptance test.
