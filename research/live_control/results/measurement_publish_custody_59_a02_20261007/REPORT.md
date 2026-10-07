# Measurement publish failure custody — A02

## H

When an executor step fails with an exception carrying structured `measurement_publish_error` metadata, ExecutorV13 must preserve that metadata on the terminal release record while keeping the original step exception primary. Cleanup may succeed or fail; its outcome must not erase the earlier publication failure.

## T

Use the actual ExecutorV13 with a controlled in-memory backend. Raise `OSError("DOWN acknowledgement lost")` with a two-field measurement publication error, run the cleanup path, and inspect the emitted terminal record. Then run the full ExecutorV13 suite and attempt the related release backend/session composition suites.

## D

- RED: the new targeted test failed because `terminal.release.measurement_publish_error` was absent; terminal status remained failed and its primary error named the original DOWN acknowledgement loss.
- Interim candidate repair: ExecutorV13 copied structured measurement publication error metadata into `terminal.release`; its targeted regression passed 1/1 and the V13 suite passed 14/14. The candidate sources are preserved under `interim_candidate_source/` and pinned to commit `e26434b7df1d2aa3d57e12e09945898e4e6ca8bb`.
- Remediation handoff: subsequent Issue #59 work produced PR [#8269](https://github.com/Unjuno/agent-interface/pull/8269), which preserves bounded `{type, message}` fields at the top level of the terminal record and adds an executor-level regression. That is the current remediation candidate; this PR keeps the RED evidence and does not carry the duplicate interim code/test patch.
- The PR #8261 source-stack checks below validate the interim candidate only; they do not revalidate PR #8269's implementation.
- After removing the duplicate interim code/test patch from PR #8259, its executor baseline suite passes 13/13; raw output and exit code are retained.
- The wider attempted composition command failed (31 failures, 1 error) because selected Doom batch-composition suites expect the `up_batch` owner implementation from `input_owner_v12.py`, which is untracked and absent from `main` in this checkout. Preserve this as a mixed-source integration limitation, not as a passing run or a regression caused by this patch.
- Python byte-compilation and `git diff --check`: PASS.

## Follow-on source-stack check (2026-10-07)

To separate the checkout mismatch from the custody change, the commit was cherry-picked into a disposable detached worktree at PR #8261 head `d9dc9dbfa09d89f10961e7cd7a8f52283b1c24c1`. The resulting candidate was `d752fe8313b6d3444fc77038abdf1ada1dea68b8`; its `executor_v13.py` SHA-256 is identical to this report's candidate source.

- `python -B -m unittest test_executor_v13 -q` from `research/live_control`: PASS (14/14).
- `python -B -m unittest test_input_owner_v12_key_measurement -q` from `research/live_control`: PASS (9/9).
- The newer batch-composition test cannot import the historical `research.observation_gating.exact_gate` dependency: that source is absent from the PR #8261 tree and main. It is not copied from an archived fixture to force a pass.
- The combined older Doom release-backend suites still fail on their legacy fake-owner `up_batch` expectations and a hard-coded current-source comparison. This limits broad suite transfer; the V13 custody suite and the current V12 measurement suite remain independently green on the actual PR #8261 source stack.

Raw output and exit codes for the two passing source-stack tests are retained below. This remains construction evidence; it does not test live X11 or the game.

## C / U

This is deterministic in-memory executor construction evidence of a terminal serialization omission and a superseded interim repair. It does not test an X server, Doom, GUI input, physical release, measurement sink durability beyond the supplied exception metadata, model inference, useful feedback, recovery, or task effect. It does not satisfy Issue #59's current-main live threat-control experiment. The broader mixed-source suite remains unverified as a coherent candidate.

## Commands

- RED: `python -B -m unittest research.live_control.test_executor_v13.ExecutorV13Tests.test_terminal_preserves_measurement_publish_failure_custody -v`
- Targeted: same command after the repair.
- Executor: `python -B -m unittest research.live_control.test_executor_v13 -v`
- Focused composition: `python -B -m unittest research.doom.test_release_backend_v3_actual_composition research.doom.test_release_backend_v3_composition research.doom.test_session_map01_v13_release_telemetry research.doom.test_session_map01_v15 research.live_control.test_executor_v13 -v`
- Construction: `python -B -m py_compile research/live_control/executor_v13.py research/live_control/test_executor_v13.py`
- Hygiene: `git diff --check`

Raw command output, exit codes, interim candidate source snapshot, and SHA-256 hashes are retained in this directory. The SHA list covers the candidate snapshot, current baseline sources, report, and primary RED/PASS/suite outputs, including the source-stack follow-on.
