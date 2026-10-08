# V39 in-flight observation versus terminal boundary (A01)

## H/T/D/C/U

- **H:** A policy observation can be emitted and decoded before the future-completion snapshot but enqueued just afterward if the sole reader is paused between decode and `incoming.put`. Because it precedes the matching terminal on the same stream, the subsequent wait should process it before terminal acceptance and final admission should reject the stale answer.
- **T:** Execute the exact current-main bounded-drain helper, nested `wait`, and final-admission functions under that delayed-reader schedule. Separately AST-audit the pinned session emitter, observation backend, executor loop, controller reader, and active observation-producer call sites.
- **D:** PASS if the snapshot is empty, the subsequent wait returns policy invalidation before terminal, actual final admission returns `REJECTED_POLICY_INVALIDATED` without authority, and terminal release is verified empty. The source audit must establish one-reader FIFO and that active observations are emitted synchronously inside backend execution, before terminal publication.
- **C:** Deterministic source-composition and static source-order evidence. It does not measure live pipe latency, HUD cadence, physical input, or game outcome.
- **U:** No live threat exposure, OS-level release, useful feedback, recovery efficacy, task effect, or MAP01 outcome was measured.

## Result

`PASS_INFLIGHT_OBSERVATION_INVALIDATES_BEFORE_TERMINAL`. At future completion, the bounded queue snapshot was empty while the exact nested stdout reader extracted from the pinned controller was paused at `incoming.put` with a decoded health-60 JSON line. After the gate opened, the real reader function enqueued that line and then the following cancelled terminal line. The subsequent wait received the observation first. The frozen current-main final-admission helper and v1/v2 decision functions returned `REJECTED_POLICY_INVALIDATED`, with no input authority; terminal release had empty keys/buttons and `verified: true`.

The source audit pins the current-main production chain. The session emitter serializes and flushes each JSON line under a lock. A single stdout reader decodes and enqueues each line before reading the next. Active observation producers run synchronously inside `backend.execute`, and both the default v12 executor path and opt-in v13 path emit terminal only after that call returns. The v15 route also replaces the backend with a release-batch wrapper; its execute method delegates synchronously through the typed-release wrapper into the same coast observation path, without creating a worker or submitting observation work. The current controller's finish path has no observation snapshot, and its fixture snapshot is disabled in the measured route. Therefore an observation can validly arrive after the future-completion queue-size snapshot, as this experiment models, but an observation emitted before its matching terminal cannot be published after that terminal in the pinned session route.

This narrows the synthetic schedule in #8435: a policy observation that is already in stdout but not yet enqueued at queue-size time is reachable, and the wait path handles it safely before terminal. A post-terminal observation in the same session stream is not supported by the audited producer path. This does not establish live pipe timing, threat response, or task success. No production code changed.

## Reproduction

From repository root on Ubuntu WSL:

```sh
python3 research/doom/v39_inflight_observation_terminal_order_a01_20261008/run_candidate.py
python3 -m unittest -v research.doom.v39_inflight_observation_terminal_order_a01_20261008.test_inflight_order
python3 -O -m unittest -v research.doom.v39_inflight_observation_terminal_order_a01_20261008.test_inflight_order
python3 research/doom/v39_inflight_observation_terminal_order_a01_20261008/audit_runtime_order.py
python3 research/doom/v39_inflight_observation_terminal_order_a01_20261008/audit_result.py
```

`FREEZE.json` pins the controller, admission, session, backend, and executor source identities.
