# V39 completed-future observation drain regression — A01

## H / T / D / C / U

- **H:** The current-main V39 queue drain can miss a hard-crossing observation produced while it processes the initially sized backlog. If the matching cover terminal was already consumed, the planner answer may reach the next action-admission path with an older frame. Draining newly enqueued events within a fixed work bound should surface that invalidation before answer admission; if the queue remains live past the bound, the controller must fail closed before reading/admitting the planner answer.
- **T:** Against exact current-main source at base `6ea1269defb6d48a607f13b08f1aa2d223ba06e9`, run `test_map01_completed_future_drain_v1.py`. The deterministic monitor inserts sequence 12 while sequence 11 is being processed. Separately, a continuously refilled queue tests the hard event cap. Run the new test in normal and optimized Python, then run the existing V39 controller, wait, and paired-signal regressions.
- **D:** Source before the change: controller blob `f7b66279d87ebc3704ccef1b6a5ce646611c890b`; ExecutorV12 blob `7e9bb6286d5f674108688ba092300a8ad2421ba9`. The first test run against the unmodified source produced one failure and one error: sequence 11 remained the reported latest frame, and the bounded-drain outcome fields were absent. Candidate source and test identities are recorded in `SHA256SUMS`.
- **C:** Pass only if the exact drain reports sequence 12 and its hard invalidation, the main caller carries that latest frame forward and branches to discard/replan before fresh action admission, and continuous production reaches the 256-event cap and raises a bounded error before consuming the planner result. Existing scoped V39 regressions must remain green.
- **U:** This is deterministic source-level construction evidence. The producer interleaving is injected synchronously by a test monitor; it does not measure real thread scheduling or event rates. No App Server, model, Doom game, GUI, OS input, physical release, live threat, application effect, recovery efficacy, or task completion was exercised. An observation arriving after the bounded drain has declared the queue empty remains subject to ExecutorV12's sequence admission check; this package does not measure that late-arrival path.

Exact base and candidate file identities are in `SOURCE_PROVENANCE.json`; `SHA256SUMS` binds the code, baseline replay, post-fix test outputs and audit inputs.

## Change and result

`drain_pending_observation_events` now consumes events enqueued while the drain is running, up to `COMPLETED_TURN_DRAIN_EVENT_LIMIT = 256`. The main loop propagates the newest observation before processing the completed answer. A remaining backlog raises `RuntimeError` before `future.result()` is consumed, so the candidate answer cannot proceed to action admission. If the newly drained event invalidates the cover after its terminal was already consumed, the existing invalidation branch discards that answer and continues the outer decision loop, whose next iteration refreshes the source from the propagated latest observation.

The regression passed in normal and optimized Python. The original implementation's failure was reproduced against the immutable source blob; exact output, base-source copy, and test copy are retained under `results/baseline-01/`. Post-change results and command exit codes are retained under `results/postfix-01/` alongside the independent audit. This is a construction result only and does not replace Issue #59's live threat-exposure requirement.

## Reproduction

Run from the repository root:

```powershell
python -m unittest discover -s research/doom -p test_map01_completed_future_drain_v1.py -v
python -O -m unittest discover -s research/doom -p test_map01_completed_future_drain_v1.py -v
python -m unittest discover -s research/doom -p test_map01_overlap_controller_v39_dual_signal.py -v
```

To reproduce the pre-fix baseline against the exact source blob from Git:

```powershell
python research/doom/v39_completed_future_drain_a01_20261008/run_baseline.py
```

Rebuild the evidence manifest and independently audit the retained outputs with:

```powershell
python research/doom/v39_completed_future_drain_a01_20261008/write_manifest.py
python research/doom/v39_completed_future_drain_a01_20261008/audit.py
```

The exact current-main starting point is commit `6ea1269defb6d48a607f13b08f1aa2d223ba06e9`. This is a repair/construction check, not a new live allocation or formal performance experiment.
