# Current-main Fake X delayed-DOWN recovery regression — R01

## Scope and classification

This is a local rerun of one existing process-level regression test in normal
and optimized Python. It is **synthetic regression evidence**, not a new formal
allocation, live GUI experiment, or reliability estimate. It tests whether a
delayed old-generation key-down observed during a canceled operation's recovery
horizon keeps the owner fenced and the public result conservative.

## Frozen source and conditions

- Current main at execution: `6684486163046b699ade1d376f35cbd222199a38`
- Host shell: Windows PowerShell; Python `3.11.9`
- Test: `runtime.guarded_win32_v1.test_process_cancellation.ProcessCancellationTests.test_delayed_down_during_recovery_horizon_keeps_owner_fenced`
- Test module Git blob: `79fb5fe2ae4ace9b6c5f27d13aade373d032b2b9`
- `process_cancellation.py` Git blob: `e58cc6e06e2ab35e1a1fbd13a5eb1821babc64ac`
- `operation_owner.py` Git blob: `8e61c0aa1c4684957c55a1b1c087675e1af56ea3`
- Test configuration in source: spawned fake producer/recovery/observer processes;
  250 ms late-input observation horizon; 20 ms sample interval; 3.5 s cleanup
  deadline.
- No Docker, WSLc, provider, real OS input, application, or external resource
  was used.

The test observes an initial neutral readback, injects a delayed fake DOWN,
observes it, and asserts owner phase `unknown`, `release_confirmed=false`,
`task_success=null`, `replay_allowed=false`, the synthetic DOWN still present,
ordered receipts, and refusal of a new operation. Teardown then clears the fake
state and joins the helper processes. This demonstrates fail-closed owner
fencing under this test schedule; it does not demonstrate successful physical
release or a real backend's delivery timing.

## Results

| Mode | Result | unittest duration |
|---|---|---:|
| Normal | 1/1 PASS | 0.886 s |
| `python -O` | 1/1 PASS | 0.799 s |

Both captured stdout transcripts are retained in `raw/`. The commands were:

```text
python -m unittest runtime.guarded_win32_v1.test_process_cancellation.ProcessCancellationTests.test_delayed_down_during_recovery_horizon_keeps_owner_fenced
python -O -m unittest runtime.guarded_win32_v1.test_process_cancellation.ProcessCancellationTests.test_delayed_down_during_recovery_horizon_keeps_owner_fenced
```

No independent auditor or mutation campaign was run. The assertions are those
of the existing test itself. No test code or runtime code was changed.

## Raw custody

`conditions.json` records the exact source identities, invocation, scope and
observed outcomes. `raw/normal.stdout.txt` and `raw/optimized.stdout.txt` retain
the command output copied from the execution transcript. This packet does not
claim a preregistered scientific experiment or a new allocation ID.
