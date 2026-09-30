# Formal06 disposition correction — protocol deviation

This addendum supersedes any wording in the original Formal06 README, Issue comment, or PR #5584 that calls the retained run a preregistered/formal result.

## Finding

The immutable allocation directory `results/formal06-20261001-01/` existed before the Formal06 freeze in Issue #5236 comment #5914754729. Its `raw.json` and `wrapper.json` filesystem timestamps are 2026-09-30 15:50:23 UTC. The freeze was posted later; the subsequent runner invocation returned `STOP_OUTPUT_COLLISION` before launching input. Thus no run was authorized and executed under that freeze.

Disposition: **STOP_PROTOCOL_DEVIATION**. Do not treat the observed values as a formal conclusion or use them to satisfy the registered decision gate. Do not rerun or replace this consumed output allocation.

## Preserved diagnostic evidence

The pre-existing wrapper records returncode 0, timeout false, child raw available, and source manifest matching the candidate source. The auditor reports `FAIL_STALE_MAP_EFFECT`: the control saved `a_`, JP→US saved `a`, and US→JP saved `a=`; both remap actors exited 0 and releases were verified. The six corruption controls were all rejected. This is a retained diagnostic observation only, because execution predates the issue freeze.

- raw SHA-256: `4548218f95fac1ea6fcef1766f1897b002b34a5dad8b36c3e608bc4453cddeeb`
- wrapper SHA-256: `8e474a9df719cca8909ee39e94e9420c817b2fe78639e8a66962daf23c5f1eb1`
- frozen auditor output: `FAIL_STALE_MAP_EFFECT` (diagnostic only)
- post-freeze attempted invocation: `STOP_OUTPUT_COLLISION`, no experiment input

Raw, wrapper, auditor output and corruption report remain unchanged. Formal05 and other predecessor evidence are unaffected. Any new formal evaluation requires a distinct successor allocation, new output path, and an Issue freeze posted before execution.