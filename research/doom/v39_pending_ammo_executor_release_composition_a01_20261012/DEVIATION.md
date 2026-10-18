# Deviations and limits

- The selected backend is deterministic and in-memory. Current-main InputOwner v12 and its V3/V4 wrappers run unchanged against a fake Xlib/XTest implementation, so `query_keymap` values describe only that fake server.
- The immediate-action minimum-ammo value 5 is a synthetic contrast. The fixture does not exercise the action-admission gate and does not assert that this threshold constrains an already admitted cover.
- Candidate output includes an `order` list as a planned label. Do not use that list as raw timing evidence. The test directly asserts Executor cancel command before planner interrupt, owner release timestamp no later than `input_released`, and `input_released` no later than terminal.
- WSLc reports swap cgroup limits unavailable. `--memory 512m` was requested; no memory/swap enforcement claim is made.
- No live allocation, model call, Doom process, real X server, physical input, useful task feedback, recovery, task effect, or MAP01 progress was used.

- Audit v1 initially returned `AUDIT_FAIL` because it inspected only stdout for unittest status; WSLc emitted those test lines on stderr. This audit-only failure is preserved under `results/audit_v1.*`. `audit_composition_v2.py` checks stdout and stderr independently, verifies the unchanged candidate and main-source hashes, and passes; its raw output and exit are under `results/audit_v2.*`. The candidate was not rerun to repair the auditor.
