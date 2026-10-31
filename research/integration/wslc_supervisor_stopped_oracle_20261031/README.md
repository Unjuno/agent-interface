# Stopped-Xvfb supervisor: reach the independent task oracle

PR #9972 retained b03, where the opt-in prestarted supervisor timed out during a private Xvfb stop and the integration test stopped early because it unconditionally expected the non-supervisor `not_attempted` release state. This change makes that intermediate assertion mode-specific: the prestarted timeout must report `unknown`, reason `transaction_deadline`, and a retired worker; the existing no-supervisor `not_attempted` assertion is retained. The existing old-task and fresh-task success assertions are unchanged. This does not add or modify runtime recovery.

Two new single-attempt, sequential Docker/WSLc trials used the same base runtime subset, edited test, image, private synthetic Xvfb, 2 CPUs, 2 GiB, 256-pid limit and no network:

| Trial | Supervisor | Test exit | Old independent task oracle | Fresh-target oracle | Final isolated cleanup |
|---|---|---:|---|---|---|
| b04 | on | 1, FAIL | FAIL: `a` remains down through horizon | not reached | `a`, `b` up |
| b05 | off | 0, five tests pass | FAIL as explicitly expected by this control | PASS | `a`, `b` up |

In b04 the supervisor's stopped-server worker retired at its transaction deadline; release remained unconfirmed and replay forbidden. After resume, the independent parent X client saw the expected application effect but also `a` held in both release and horizon readbacks. The unchanged supervisor-mode task-success assertion failed, so b04 does not establish fresh-target recovery. Both trial final cleanups were explicit harness cleanup and do not retroactively make the old task successful. A real earlier key-release event alone did not establish a neutral key state.

The prior b03 failure, source and conditions remain in PR #9972; b04 uses a distinct allocation and a targeted test-only edit rather than rerunning it. These are single, fixed-order synthetic observations, not a reliability or MAP01 result, nor proof of safety on a shared X server. Later recovery must fence stale requests and respect newer clients' input. `public.zip` retains conditions, runners, raw stdout/stderr, launcher results, full receipts and per-file hashes. `python audit.py` verifies these outcomes. The manifest pins the main source subset archive and edited test hash; the rest of the mounted source and image bytes are not archived here.
