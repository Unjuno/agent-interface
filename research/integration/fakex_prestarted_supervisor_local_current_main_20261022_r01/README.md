# Public-caller Fake X supervisor regressions — 2026-10-22 r01

## Scope and claim

This is a local synthetic Fake X regression packet, not a live X server or GUI experiment. It re-runs the existing public MCP caller tests for one healthy release, bystander reuse refusal, stale-generation refusal, and a blocked cleanup supervisor that expires. It verifies bounded caller response and conservative outcomes around blocked I/O. It does **not** prove physical input release, release while a real X server is globally blocked, task success, MAP01, a reliability rate, or WSLc behavior.

The healthy Fake X path records exactly one key-up effect and a test-side independent readback. The runtime receipt remains `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`. Bystander and stale-generation cases refuse without a release effect. When the cleanup worker remains blocked past its transaction deadline, the public call returns in 0.250–0.266 seconds, the worker is retired, Fake X records no release, and the result stays UNKNOWN. This confirms bounded caller behavior and fail-closed classification for these synthetic schedules; it does not establish that blocked platform I/O can be safely released.

## Frozen conditions

- Repository main before this doc-only receipt: `03116d190138dd3e33762ad15c04d91d8fd0ddf9` (PR #9347 adds only this receipt document; the three runtime test/source files below compare byte-for-byte with that main commit).
- Runtime files: `runtime/cli_v1/test_mcp_owned_process.py`, `runtime/guarded_x11_v1/test_cancel_supervisor.py`, and `runtime/guarded_x11_v1/cancel_supervisor.py`.
- Host: Windows 10; CPython 3.11.9 at `C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe`.
- Pillow/Xlib and other imports came from the local Python environment; no external GUI, WSLc, Docker, model/provider, network, or physical input was used by the tests.
- Test command in both modes:
  `python [-O] -m unittest runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_prestarted_supervisor_public_path_releases_once_but_keeps_runtime_unknown runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_prestarted_supervisor_public_path_preserves_bystander_refusal runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_prestarted_supervisor_rejects_stale_generation_without_effect runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_prestarted_supervisor_deadline_kills_blocked_worker_and_preserves_unknown runtime.guarded_x11_v1.test_cancel_supervisor.PrestartedCancellationSupervisorTests`
- Each mode wrote its own test log and compact structured trial records under `normal/` or `optimized/`; no files were overwritten between the final paired runs.

## Outcome

- Normal Python: 15 tests passed in 13.393 s.
- Optimized Python (`-O`): 15 tests passed in 14.099 s.
- `healthy-release.json`: one Fake X `KeyRelease`, keys up in Fake X readback, duplicate operation reused; runtime release/task-success claims remain false/null.
- `stale-generation.json`: zero accepted effects, one refusal with `stale_generation`, release not attempted.
- `blocked-helper-deadline.json`: no accepted release effect, key remains down in Fake X, owner worker retired, UNKNOWN, replay denied. Caller response was 0.266 s normal and 0.250 s optimized.
- Bystander-reuse refusal is covered by the named public-caller test and both passing suite logs; it asserts the action is refused with no effect.

The top-level JSON/log files in this packet root came from a preliminary combined invocation that reused one evidence directory for both interpreter modes. They are retained for audit but excluded from the paired outcome above; the mode-separated subdirectories are the authoritative artifacts.

## Interpretation and next gate

The test suite distinguishes caller responsiveness, synthetic release effect/readback, and runtime authorization. Its blocked-supervisor case proves that a deadline can retire a blocked worker without inventing a release. The healthy case demonstrates only Fake X behavior with a blocked owner fixture. A separate helper-only late-resume probe held the existing Fake X worker until 16 ms after its absolute deadline, then resumed it. In both normal and optimized Python it returned `expired_deadline`, recorded zero accepted effects and one refusal, and left the key down. This checks the helper deadline guard only; it does not exercise supervisor process termination, a live X server, or a global X-server I/O stall. Keep the supervisor default-off and retain the UNKNOWN/replay-denied boundary.

## Hashes

See `SHA256SUMS.txt` for the mode-separated raw logs and JSON records, including the late-resume probe. Runtime source blob IDs from the stated main commit are included there as well.

