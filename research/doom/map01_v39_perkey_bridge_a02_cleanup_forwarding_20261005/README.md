# MAP01 V39 per-key cleanup forwarding bridge A02

This additive bridge candidate drains asynchronous InputOwner V13 cleanup records and turns a scoped per-key cleanup measurement into the V39 consumer event shape. It preserves the source owner cleanup record, original program/step context, owner/intent/key identity, and actuation ID. An adapter edge is emitted only for a confirmed ordered physical-up sample bracket. Unknown lineages are retained as unscoped diagnostics. The bridge suppresses a later `NOOP_ALREADY_UP` receipt when its corresponding cleanup was already forwarded.

## H / T / D / C / U

- **H:** V39's current synchronous-only bridge drops a verified asynchronous cleanup edge. A cursor-based owner-record drain can forward it once with its admission context and prevent a duplicate no-op release row.
- **T:** One frozen bridge invocation against the V13 owner and fake-display harness: admit F8 down, cancel the lease, await owner-thread cleanup, then call F8 up. No retry.
- **D:** PASS only if the fake display is neutral, one contextual release measurement carries the same actuation ID and the confirmed physical-up interval, the cleanup source row is retained, and no no-op row duplicates that release.
- **C:** Synthetic bridge and fake-display behavior only. This does not establish deployment in a live v39 process, real X11 behavior, application consumption, benefit, or authorization for a live allocation.
- **U:** One key and one cancellation interleaving; no GUI, OS input, game, model, or application effect.

The owner is drained before and after each synchronous input operation, in `execute`'s `finally`, and on both sides of inherited backend shutdown. The cursor ensures records are emitted once even if multiple drains see the same owner list.

## Reproduction

```powershell
python -m unittest -v research.doom.map01_v39_perkey_bridge_a02_cleanup_forwarding_20261005.test_bridge
python -m unittest -v research.doom.map01_v39_perkey_bridge_a02_cleanup_forwarding_20261005.test_teardown
python -m unittest -v research.doom.map01_v39_perkey_bridge_a02_cleanup_forwarding_20261005.test_execute_context
python research/doom/map01_v39_perkey_bridge_a02_cleanup_forwarding_20261005/run_candidate.py
python research/doom/map01_v39_perkey_bridge_a02_cleanup_forwarding_20261005/audit.py
```

The initial candidate output is retained under `results/a02/`. An independent strict-consumer audit successor uses a fresh one-shot run retained under `results/a03/`; neither output is overwritten. This is additive to, and does not alter, the frozen A01 bridge or its results.

The focused teardown test separately closes a backend while F8 is held and checks that the owner-thread close record is forwarded after the owner stops, with the original context and a neutral fake display. It does not rerun the retained candidate.

The supplemental execute-context test calls the candidate's actual
`Backend.execute()` wrapper around a fake inherited executor. The fake executor
admits F8, requests lease cancellation, and waits for the V13 owner cleanup;
the wrapper's `finally` must drain exactly one confirmed contextual up before
clearing its context. This does not claim that the candidate is wired into
`session_map01_v12.py`; current main still selects the V10 typed-release
backend.
