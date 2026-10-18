# V39 ordinary cover terminal validation

V39 previously renewed a cover after a `failed` terminal while its planner was
pending, and could reach final action admission after a failed or unverified
post-answer cancellation terminal. The policy-invalidation cancellation path
already checked neutral closure (#7960); these ordinary paths did not.

The candidate requires `completed` or `expired` plus verified empty keys and
buttons before renewal. After the planner completes and cancellation is sent,
`cancelled` is also allowed. Invalid terminals raise before another submit or
final admission. A pending planner receives an interrupt request before the
thread-pool context waits for it; secondary interrupt exceptions do not replace
the terminal failure.

This is a controller contract repair, not a game-policy or guard-threshold
change. Actual owner fencing is separate. No unsafe native input was observed.

## Source and scope

- Scientific parent: [#59](https://github.com/Unjuno/agent-interface/issues/59).
- Baseline: [#8261](https://github.com/Unjuno/agent-interface/pull/8261),
  `4190104d0c72a025093c8569fdbd216b5929de0b`.
- Observed main: `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.
- Controller SHA-256:
  `16b2c3e863f2c28f197425d7fa0fc6dd24dc25dcfcfcd8f8344b7acfbe671ccd`.
- Regression SHA-256:
  `cb4757613caf43380b46d2cfe63e1788511fc93b3e9c60789f17b9a582f50968`.
- Host: macOS 27.0.1 arm64, Python 3.12.14, Pillow 12.3.0, NumPy 2.3.5.
- Existing root and bugbot workers only. No VM, container, GUI, OS input,
  external model call, or formal/live allocation was used.

The fixture executes actual V39 `main` and a real `ThreadPoolExecutor`, with
synthetic planner/session transport and a cleanup-entry spy. One case connects
actual ExecutorV13 to the controller through JSON serialization using an inert
backend that raises an `OSError`. Positive controls stop at a sentinel before
performing downstream renewal or final admission.

H: malformed, failed, decision-required, or nonneutral cover closure must stop
ordinary continuation; legitimate neutral completion/cancel races must continue.
T: deterministic schedules for pending, renewed, already-completed, and
completion-racing planner futures; compare unchanged baseline with candidate.
D: all 21 negative schedules stop before later admission, and all five positive
controls reach their expected continuation boundary. C: distinguish a controller
attempt to submit from actual OS input, and neutral cleanup from successful
program execution. U: no native-input, game-benefit, or model-latency inference.

## Retained outcomes

| Attempt | Result |
|---|---|
| `baseline.log` | Initial fixture error: missing `authored` admission key, 24 setup errors; no semantic result |
| `baseline-v2/`, log | Corrected fixture on unchanged production baseline: 19 negative cases fail, five positive controls pass |
| `candidate/`, log | Same 24 schedules pass with the controller repair |
| `baseline-v3/`, log | Two added producer/exception-custody cases fail on the saved baseline controller |
| `candidate-v2/`, log | All 26 schedules pass, across nine unittest methods |
| `related-tests.log` | 56 existing V39 methods pass |
| `closure-tests.log` | 20 renewal, paired-dispatch, and cleanup methods pass |
| `index-tests.log` | 22 workspace index methods pass |
| `optimized-tests.log` | Nine new methods pass under `python -O` |

Compilation, `git diff --check`, and the committed workspace index check pass
(160 top-level research directories). Remote CI is not claimed.
Bugbot's read-only source review and saved-trace comparison found no material
regression; this is not a FINAL-v5 nonauthor quorum or integration vote.

The interrupt-error fixture releases its future before raising. Production
`PersistentPlannerAdapter.interrupt` can return `request_error`; the existing
90-second `await_turn` timeout may still govern pool shutdown in that case.
Prompt completion on delayed or failed interrupt transport is not established.
The cleanup spy does not verify physical release or production teardown.

## Reproduce

From this candidate checkout, use Python with Pillow and NumPy available:

```bash
export PYTHONPATH=research/doom:research/live_control:research/observation_gating:research/tiles:research/real_apps_v1
python -m unittest research.doom.test_map01_overlap_controller_v39_cover_terminal -v
python -O -m unittest research.doom.test_map01_overlap_controller_v39_cover_terminal -v
```

Set `V39_COVER_TERMINAL_TRACE` to a new empty output directory to retain traces.
The unchanged baseline controller and the tested fixture revisions are inside
the archive. `baseline-v3` executed that saved controller in a module whose
`__file__` remained the repository controller path, preserving dependency and
resource lookup, then ran the two added test methods. Baseline runs are expected
to fail the new continuation assertions.

## Evidence custody

[`RESULT.json`](RESULT.json) records outcomes and limitations.
[`MANIFEST.json`](MANIFEST.json) records every archived member and its hash.
[`evidence.tar.xz`](evidence.tar.xz) contains 90 members, 34,368 bytes, SHA-256
`912ff99438023c09445d72d84ddfc76abd532064ace29defe77a769c97d4825f`.
All members were read back and checked against the manifest.

Raw traces and source snapshots are exact. Public log copies replace only local
workspace paths; the manifest also records original hashes. Original logs,
including the initial fixture failure, remain in the owned local evidence
directory. The archive is passive and is not imported or discovered as tests.
No historical evidence or canonical research goal was rewritten.
