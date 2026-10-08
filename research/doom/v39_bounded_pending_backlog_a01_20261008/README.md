# V39 bounded pending-observation recovery A01

Date: 2026-10-08 (Asia/Tokyo)  
Base source: `origin/main` at `6ea1269defb6d48a607f13b08f1aa2d223ba06e9`  
Branch: `research/59-v39-bounded-pending-backlog-a01-20261008`

## H/T/D/C/U

- **H — Hypothesis:** A queue arrival during a finite snapshot drain can remain unprocessed after a pre-consumed cover terminal, causing the controller to reuse a plan from an older observation. A hard crossing in that event should invalidate the plan; stale Executor admission must remain fail-closed, and bounded recovery should use a newer full observation or stop explicitly.
- **T — Minimum test:** Replay the exact sequence 11 → (monitor callback queues typed sequence 12 with a hard health crossing) against the production drain; connect recovery to the exact ExecutorV12 `submit`. Add a replenishing queue to establish a finite-work bound. Run all V39 `test_map01*.py` tests on the patch.
- **D — Decision:** PASS for the deterministic construction if the hard crossing is observed before answer reuse, no worker starts with stale sequence 11, a newer full sequence 12 can be admitted, and continuous backlog exhausts a finite budget. No live runtime promotion follows from this test.
- **C — Competing explanation:** If the session writer cannot publish this event ordering, the reproducer is only a reachable queue schedule, not evidence it occurs in operation. The runtime may also reject an event after the bounded queue check; the Executor still prevents stale admission, but this patch does not demonstrate recovery from every post-check race.
- **U — Uncertainty:** No App Server, Doom process, model, GUI, OS input, or real threat exposure was used. Caller placement is checked by the repository test; the full `main()` lifecycle is not run. The patched admission test uses the actual ExecutorV12 method but stubs its worker thread, so “accepted” means admission only, not physical execution.

## Baseline reproduction

`baseline_reproducer.py` extracts the exact `drain_pending_observation_events` helper and exact `ExecutorV12.submit` from the pinned main sources. The deterministic schedule left sequence 12 queued, returned sequence 11 with no invalidation, skipped the caller's wait because `current_terminal` already existed, then received the exact rejection `latest observation sequence required before input`. This is a liveness/recovery defect; the stale operation was not accepted.

Pinned source IDs:

- `research/doom/map01_overlap_controller_v39.py`: blob `f7b66279d87ebc3704ccef1b6a5ce646611c890b`, SHA-256 `02a6289390837bb97198c98fe03c41c775d829bf6606fc4c11085630b3de0793`.
- `research/live_control/executor_v12.py`: blob `7e9bb6286d5f674108688ba092300a8ad2421ba9`, SHA-256 `e78440263866dd06eaf868e902ae50b08aa2b634f086bfbd412f6c338ccea2b2`.
- Captured baseline: `baseline_result.json`, SHA-256 `aeba53ab392de97ab7ba7c27eaf44af4700930cb67b95d1cc139ec85d2848263`.

## Change under test

The controller now drains at most 256 events per call and reports residual backlog. Events arriving while the queue is being processed are eligible for the same bounded drain. A hard invalidation or remaining backlog discards the current answer. Before the next decision, the controller settles at most four more 256-event batches; if no newer full observation was retained, it waits for one whose sequence exceeds the discarded plan's source. Persistent backlog ends in an explicit fail-closed error. Recovery receipt is attached to the discarded decision.

## Reproduction and outcome

From the repository root, with `research/doom` and `research/live_control` on `PYTHONPATH`:

```powershell
$env:PYTHONPATH = "$(Get-Location)\research\doom;$(Get-Location)\research\live_control"
python -m unittest discover -s research/doom -p 'test_map01*.py' -v
```

Outcome: **48 tests passed** in 0.141 s. See `unittest.log`. New cases cover a boundary hard crossing, a harmless event arriving while drain is active, the 256-event cap, a replenishing producer exhausting exactly four recovery batches, fresh-sequence recovery, and exact ExecutorV12 stale rejection followed by fresh-sequence admission. `git diff --check` and `py_compile` also passed. `sha256.json` records the source and raw artifact hashes; `audit.py` checks provenance and outcome.

## Limits and next gate

This is a deterministic construction and code-level recovery check. It does not prove that the session writer produces this interleaving, that the 256/4 limits are optimal, that every race after the final empty-queue check recovers, or that useful local control succeeds during MAP01 threat exposure. The separate Issue #59 live allocation remains unassigned and must not be invoked here. Next: reviewer-run the patch, then under an explicitly granted, newly frozen allocation instrument whether the production writer exhibits the schedule and measure recovery/release/per-key timing plus useful feedback and MAP01 outcome.