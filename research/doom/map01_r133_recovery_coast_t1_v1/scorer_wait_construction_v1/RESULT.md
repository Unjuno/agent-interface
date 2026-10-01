# Result — scorer events during delayed command delivery

## Outcome

`PASS_SCORER_EVENTS_RETAINED_DURING_COMMAND_WAIT_CONSTRUCTION`.

The one-shot WSL2/Linux host candidate ran against the exact `FREEZE.json`
hashes. A real anonymous pipe withheld the command for 350.323 ms. The retained
main-thread adapter produced 13 scorer samples with zero missed sample periods;
the scorer-only stream recorded exactly one positive
`KILL_COUNT_INCREASE` at +86.094 ms and one negative
`DEATH_COUNT_INCREASE` at +143.239 ms from wait start. Both preceded command
send. The `{"op":"finish"}` line was returned unchanged 0.758 ms after send.
No scorer payload appeared in the returned command. Candidate exit was 0.

The separate raw-only auditor independently read the immutable raw file and
returned `errors=[]`, with the same raw SHA-256:
`fd07dcb1da9810d3c842ee87889b3256068185bf808ae170b68fd5dd450e9cba`.
All three in-memory corruption controls were rejected:

- omitted event → `event_inventory`;
- `controller_visible=true` → `event_authority`;
- event time moved after command send → `event_outside_command_wait`.

Commands, source/environment hashes, complete rows, run receipt, raw output, and
audit receipt are retained in this directory. There was no retry or second
candidate/auditor invocation.

## Interpretation and limits

This establishes that the existing independent clock, main-thread polling, and
stdin/file adapter can be composed to retain state transitions during an empty
command wait without returning scorer data to the controller command stream.
The scorer is deterministic and fake; the timing interval is a test harness,
not a measured model-latency distribution.

It does **not** establish integration with `session_map01_v6.py`/v23, plan/step/
actuation lineage, game-state scoring validity, task-effect causation, physical
key-up timing, threat exposure, recovery benefit, survival, MAP01 completion, or
user-visible performance. No Docker/OrbStack, X11, ViZDoom, input, model,
provider, GPU, or shared allocation was used. The matched T1 live experiment
remains `HOLD`; the exact shared Docker lease and other preregistration/source
gates are still required.
