# V39 future-done late observation race A03

This one-shot current-main source-slice experiment schedules a matching completed terminal in the queue, then injects a typed health observation immediately after the production drain's qsize snapshot. It runs the exact completion-time branch, production final-admission adapter, and action-admission helper. The late observation remains queued while action validity is evaluated using the retained `latest` row; only afterward does the harness deliver that observation to the monitor. A01/A02 harness STOP records are retained in sibling packages.

## H / T / D / C / U

- **H:** An observation arriving after the finite backlog snapshot can remain unseen while the current-main action-admission helper evaluates the older `latest` observation.
- **T:** Execute frozen `drain_pending_observation_events`, its exact completion-time caller branch, actual final/action admission helpers, signal guard/monitor, and action validity contract under a deterministic queue interleaving.
- **D:** Record the action-admission receipt and event order. A READY result on stale health followed by a hard invalidation only after later row delivery demonstrates this schedule can reach the pre-executor READY boundary; no executor submission occurs.
- **C:** Synthetic scheduler interleaving only. It establishes a possible ordering, not frequency in a live run. No executor, input, game, GUI, or OS behavior is run.
- **U:** No live threat exposure, HUD accuracy/cadence, real response time, physical key state, recovery efficacy, progress, survival, or task outcome.

Source identities are frozen in `FREEZE.json`; previous harness STOPs are recorded in sibling A01 package.

## Reproduction

```text
python -m research.doom.v39_future_done_late_observation_a03_20261008.candidate
python -m research.doom.v39_future_done_late_observation_a03_20261008.audit
python -m unittest -v research.doom.v39_future_done_late_observation_a03_20261008.test_audit
```

Candidate outputs refuse overwrite.
