# V39 in-flight observation versus terminal boundary (A01)

## H/T/D/C/U

- **H:** If a hard-invalidating observation line precedes the matching cover terminal but is decoded just before the completed-future snapshot, the current session emitter and controller reader preserve FIFO. The subsequent terminal wait sees the observation first, and final admission rejects the completed answer.
- **T:** Execute the exact current-main bounded-drain helper, nested `wait`, and final-admission functions under a delayed-queue schedule. Separately AST-audit the pinned session emitter, observation backend, executor loop, and controller reader.
- **D:** PASS if the snapshot is empty, the subsequent wait returns policy invalidation before terminal, actual final admission returns `REJECTED_POLICY_INVALIDATED` without authority, and terminal release is verified empty. The source audit must establish that an observation line emitted before terminal is enqueued before terminal.
- **C:** This is deterministic source-composition plus static source-order evidence. It does not measure live scheduling, pipe latency, HUD cadence, or physical input.
- **U:** No live threat exposure, OS-level release, useful feedback, recovery efficacy, task effect, or MAP01 outcome was measured.

## Result

`PASS_INFLIGHT_OBSERVATION_INVALIDATES_BEFORE_TERMINAL`. At future completion, the bounded queue snapshot was empty while the test reader held a decoded observation. The subsequent wait received the health-60 sample before the matching cancelled terminal. The frozen current-main final-admission helper and v1/v2 decision functions returned `REJECTED_POLICY_INVALIDATED`, with no input authority; terminal release had empty keys/buttons and `verified: true`.

The separate source audit pins and verifies the current-main production chain: the coast backend emits observations synchronously inside `backend.execute`; Executor emits terminal only after `backend.execute` returns; the session emitter serializes and flushes each JSON line under a lock; the controller has a single stdout reader that enqueues each decoded line before reading the next; and `wait` passes observations to the monitor before checking the terminal predicate. Thus the same-stream FIFO condition is supported by implementation, not merely assumed. This does not establish real pipe timing or a live threat response.

This is distinct from PR #8431 and PR #8435, which test observations already enqueued at completion. Here the line is decoded but remains outside the queue during the bounded snapshot, then is inserted before its following terminal line. No production code changed.

## Reproduction

From repository root on Ubuntu WSL:

```sh
python3 research/doom/v39_inflight_observation_terminal_order_a01_20261008/run_candidate.py
python3 -m unittest -v research.doom.v39_inflight_observation_terminal_order_a01_20261008.test_inflight_order.py
python3 -O -m unittest -v research.doom.v39_inflight_observation_terminal_order_a01_20261008.test_inflight_order.py
python3 research/doom/v39_inflight_observation_terminal_order_a01_20261008/audit_runtime_order.py
python3 research/doom/v39_inflight_observation_terminal_order_a01_20261008/audit_result.py
```

`FREEZE.json` pins the controller, admission, session, backend, and executor source identities.
