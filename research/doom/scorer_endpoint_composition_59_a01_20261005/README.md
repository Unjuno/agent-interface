# Scorer endpoint composition candidate A01

This construction check composes two retained findings for Issue #59:

- **H:** V16's acknowledged producer path could preserve update/run identity
  while qualifying kill/death counts only from a single `GameState` whose tic
  equals the acknowledged episode endpoint.
- **T:** compose a state-backed sample function with the exact retained V16
  sampler and sink, using the neutral ASYNC_SPECTATOR 1→11 record plus malformed
  and mismatched fake boundaries; no second game allocation is started.
- **D:** accept only when producer update returns with positive tic progress,
  sample snapshot tic matches the unchanged episode endpoint, configured enum
  order is known, and counter values are finite nonnegative integers. Mismatch
  or malformed evidence (including boolean tic values) must publish no scorer
  sample.
- **C:** this tests the composition boundary that the earlier one-tic checkpoint
  helper and V16 getter sampler did not jointly exercise. It does not test
  changed score values or controller/task behavior.
- **U:** all V16 composition tests run as native Windows fake-game construction
  because `wslc.exe` is unavailable and the Docker Linux daemon is stopped; no
  resource enforcement or engine run is claimed. Host detail is in `HOST.json`.

- `scorer_checkpoint_tic_ack_t0_v1/candidate.py` requires an exact one-tic
  refresh before its status qualifies. Its repair prevents status-only
  acceptance of a no-op, multi-tic interval, or tic drift during value reads.
- `scorer_async_spectator_59_t0_a01_20261004/raw.json` records one acknowledged
  ASYNC_SPECTATOR update from episode tic 1 to 11, with `GameState.tic == 11`.
  Thus the earlier exact-one-tic predicate rejects this observed coherent
  endpoint interval.

`checkpoint_candidate.py` retains the executor lock/neutral-owner checks and
finished-episode refusal, accepts any positive acknowledged tic advance only
when the `GameState` tic equals the post-update episode tic and that endpoint
remains stable through the snapshot read, and returns only a status receipt.
Scores remain in the private event log. Failed qualification removes score
values from the record. The fixture test composes the new candidate against the
actual retained JSON while exercising one-tic, no-op, endpoint mismatch, and
read-drift boundaries. The candidate also verifies configured game-variable
order before interpreting the `GameState` vector, as required by ViZDoom's
`set_available_game_variables` / `get_available_game_variables` contract
([official API reference](https://vizdoom.farama.org/api/python/doom_game/)).

The second rung composes `state_snapshot_sampler.py` with the exact retained
V16 `AcknowledgedSampler`, `ProgressClock`, and `ScorerFileSink`. It reads
kill/death counters from one `GameState`, checks that its tic matches the
acknowledged update endpoint, and keeps the V16 producer receipt and scorer-only
sink. The positive fixture uses the retained neutral 1→11 interval; mismatch,
missing/duplicate counters, fractional values, and boolean tics fail closed.
This checks component composition only; it does not run the ViZDoom engine or
V16 session.

`session_map01_v17.py` is an opt-in wrapper following the retained V16 session
pattern: it installs `AcknowledgedSampler(coherent_snapshot_sample, ...)` into
the unchanged V15 session callback, writes scorer client-update receipts, adds
candidate source hashes to the run manifest, and restores the prior sampler in
`finally`. Tests exercise installation, manifest binding, and restoration on
normal return and session exception. It has not run against the Doom engine or
the real V15 controller dependencies.

Run from the repository root:

```powershell
python -m unittest discover -s research/doom/scorer_endpoint_composition_59_a01_20261005 -v
python -m py_compile research/doom/scorer_endpoint_composition_59_a01_20261005/checkpoint_candidate.py research/doom/scorer_endpoint_composition_59_a01_20261005/state_snapshot_sampler.py research/doom/scorer_endpoint_composition_59_a01_20261005/session_map01_v17.py research/doom/scorer_endpoint_composition_59_a01_20261005/test_candidate.py research/doom/scorer_endpoint_composition_59_a01_20261005/test_state_snapshot_sampler.py research/doom/scorer_endpoint_composition_59_a01_20261005/test_session_map01_v17.py research/doom/scorer_endpoint_composition_59_a01_20261005/audit.py
python research/doom/scorer_endpoint_composition_59_a01_20261005/audit.py
```

`test-output.txt` and `audit.json` retain this construction run and its
independent source-pin/test-log audit. The audit does not independently
reimplement the candidate or qualify a live engine.

The result is synthetic construction evidence using a retained runtime record;
the helper was not integrated into a running MAP01 controller. A01 had unchanged
KILLCOUNT and DEATHCOUNT. Changed-score freshness, useful task feedback,
invalidation recovery, physical input release, planner resumption, bounded
recovery, and a live MAP01 outcome remain unproven. This candidate grants no
input authority and must be integrated and tested in the actual controller
before runtime qualification.

The post-read endpoint is also checked for exact `int` type before equality.
Python considers `11.0 == 11` and `True == 1`, so equality alone could retain a
snapshot whose closing tic did not have the required integer representation.
`test_post_read_tic_requires_exact_integer_type` reproduces both cases; the
candidate returns `UNKNOWN` and removes private score values. On the exact PR
head used for this regression, the new test failed for both inputs before the
guard and passed afterward. The documented package discovery run then passed
16 tests; see `test-output.txt`. This adds only fake-game type-boundary evidence.