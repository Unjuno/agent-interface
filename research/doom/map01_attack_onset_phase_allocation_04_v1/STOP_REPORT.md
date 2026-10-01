# Issue #4223 allocation 04 — formal runtime STOP

## Disposition

The sole frozen formal orchestration was consumed and stopped in `p1-immediate` before its first `ready` event or observation. The runner returned `FAIL_FORMAL_RUNTIME_OR_SCHEMA`, exit code 1, rows 0, formal invocations 1, reruns 0, replacements 0, and post-freeze tuning 0. This is an infrastructure/runtime STOP, not a scientific PASS/HOLD, game-task failure, or evidence favoring either onset arm. Allocation 04 must not be retried or modified.

## Raw evidence

`formal/run-01/FORMAL_RESULT.json` retains the runner result and traceback. `FORMAL_STDOUT.jsonl` retains the runner's single stdout record. The first case's `launch.json` has no event markers and records `RuntimeError('stdout closed: ')`; `controller_events.json` is `[]`; the runtime `sources.json` was written, while `setup.txt` is empty. There is no `events.jsonl`, observation, scorer stream, score, owner-event stream, physical edge, controller command, or TASK_EFFECT.

`FORMAL_EXECUTION.json` binds the exact Docker command, image digest, Linux/amd64 platform, no-network/read-only mounts, and the observed exit code. `STOP_AUDIT.json` independently reconstructs the stop boundary and verifies all 20 source hashes against runtime source base `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`; its 9/9 evidence checks pass. `test_audit_formal_stop.py` passes six cases, including corruption rejection for invocation count, arm, controller event, runtime event stream, and source hash.

## Root-cause boundary

Root cause remains **undetermined**. The frozen `run_case.py` reports closed stdout with empty stderr but does not preserve the child process exit status. Source identities are present, showing the child reached the retained session module graph, but they do not identify why it exited before `ready`. Linux/amd64 emulation on the OrbStack linux/arm64 daemon is a candidate, not a finding. Do not infer a ViZDoom gameplay or onset-phase outcome.

## Next eligible work

Any further test requires a fresh allocation and source freeze. Its non-formal runtime gate must exercise actual ViZDoom `DoomGame` initialization through the same Xvfb/Openbox/image path and retain process exit status, stdout/stderr, and the first ready/observation boundary. Imports and X display connectivity alone are insufficient. Only a passing game-start gate plus fresh public readback/ownership clearance can authorize a new one-shot formal allocation under the unchanged Issue H/T/D/C/U.
