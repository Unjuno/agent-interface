# Issue #59: retained v39 feedback data sufficiency and V15 adapter construction

This additive package separates two results: a data sufficiency HOLD on the retained v39 episode, and a CPU-only producer-composition construction using the current V15 scorer writer and release-record contract.

## T1 — retained v39 trace reprocessing

**H:** Does the immutable v39 first-outcome trace directly contain the scorer sample/event and verified per-key release records required by the #7537 temporal attribution gate?

**T:** Freeze the v39 report, raw runtime event stream, owner-release record, v39 occupancy reconstruction, and the exact #7537 gate source. Project only records already using the gate's schemas; do not turn health/ammo observations, viewport pixel changes, or the terminal scoreboard into scorer events. Run the candidate once and a separate raw-only audit once.

**D:** `HOLD_DATA_INSUFFICIENT_SCOPED`. The 634-row runtime stream has zero `independent-progress-sample-v2` rows, zero `independent-progress-event-v2` rows, and zero complete explicit per-key release intervals. It contains 218 controller-visible typed observations, four viewport-only pixel receipts, 39 input-admission rows without action/step/intent identity or a per-key release endpoint, 13 verified program-level owner releases, 29 occupancy rows, and one post-control score snapshot. That final snapshot records one kill and no MAP01 exit, but has no timed scorer sample sequence. The frozen attribution function returns no labels; this is **not evaluable**, not a PASS. Candidate and independent audit agree; see [RESULT.json](RESULT.json), [AUDIT.json](AUDIT.json), and [the frozen inputs](inputs/).

**C/U:** This does not show that no useful event occurred during the episode; it shows that the retained trace cannot locate one in time or join it to a complete per-key interval under the frozen contract. It makes no new game/model/input run, causal claim, safety claim, recovery claim, or MAP01 completion claim.

## T2 — current V15 producer-composition adapter

Current main already has an independent V15 scorer sink and per-key key-up telemetry. T2 adds `attribution_adapter_t2/adapter.py`, which normalizes those producer schemas into the previously frozen #7537 gate. The adapter joins a key down/up only by the exact `(owner_id, intent_token, program id, step, key)` identity, uses the owner-thread XSync return as the key-up boundary, validates the whole release batch's positions, and leaves incomplete or unbound traces unresolved.

The candidate exercised the real `ScorerFileSink` and `ProgressClock` source with synthetic monotonic timestamps 100 and 300 to emit two controller-invisible samples and one positive kill-count event; those fixture timestamps and the 35 Hz scheduler metadata are not a polling-rate measurement. Six keyboard scenarios used rows shaped from the current backend source: one verified intent, two overlapping intents, a mismatched release, an unverified release, a declared two-row batch with one row absent, and an unbound admission. The independent audit returned `PASS_V15_PRODUCER_COMPOSITION_SCOPED`; the T2 and frozen T0 suites passed 18/18 tests. The incomplete-batch test first failed by producing an unjustified unique label, then passed after batch-position validation was added.

A `TEMPORALLY_UNIQUE` result here means the recorded interval uniquely spans the scorer's detection bracket. It does not establish that the input caused the kill, that the input reached the application as intended, or that the scorer is useful or timely in a real session. Input rows are source-shaped fixtures; there was no game, GUI, OS input, model call, or resource allocation in T2. See [T2 README](attribution_adapter_t2/README.md), [candidate result](attribution_adapter_t2/run/candidate.json), and [independent audit](attribution_adapter_t2/AUDIT.json).

## Reproduction

Run T1 from this directory:

```powershell
python -B -m unittest -v test_t1.py
python -B run_t1.py
python -B audit_t1.py
```

Run T2 from `attribution_adapter_t2/`:

```powershell
python -B -m unittest -v test_adapter.py test_t0.py test_runner.py
python -B run_t2.py --run-dir run/replay
python -B audit_t2.py --run-dir run/replay
```

Both freezes pin the source commit and source files. Candidate, audit, test, and raw outputs are retained beside each freeze. The Issue #59 live threat-control and MAP01 gates remain open; T1/T2 do not consume or authorize the unassigned live lane. The concrete next evidence remains a fresh assigned current-V15 session retaining scorer samples/events and identity-bound per-key admission/key-up rows, followed by the separately labelled continuously advancing MAP01 attempt.
