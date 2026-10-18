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

The original A01 package **reported** 48 tests passed in 0.114 s and referred to `unittest.log`. That raw log is absent from the merged package, so the historical 48-test result is **not verified from retained raw output**; it must not be treated as a confirmed result. New cases were described as covering a boundary hard crossing, a harmless event arriving while drain is active, the 256-event cap, a replenishing producer exhausting exactly four recovery batches, fresh-sequence recovery, and exact ExecutorV12 stale rejection followed by fresh-sequence admission. The original report also said `git diff --check` and `py_compile` passed. `sha256.json` records retained source/artifact hashes; `audit.py` checks the available provenance and outcomes.

## Limits and next gate

This is a deterministic construction and code-level recovery check. It does not prove that the session writer produces this interleaving, that the 256/4 limits are optimal, that every race after the final empty-queue check recovers, or that useful local control succeeds during MAP01 threat exposure. The separate Issue #59 live allocation remains unassigned and must not be invoked here. Next: reviewer-run the patch, then under an explicitly granted, newly frozen allocation instrument whether the production writer exhibits the schedule and measure recovery/release/per-key timing plus useful feedback and MAP01 outcome.

## Current-main package audit correction (2026-10-08)

The merged package's original `audit.py` crashed because `unittest.log` is absent, although `sha256.json` listed its expected digest (`d51642c4…`). That historical 48-test output was not recovered. The gap is explicit in `historical_artifact_gap.json`; no 12-test output is substituted for it.

A separate current-main revalidation ran the focused `test_map01_v39_pending_observation_drain.py` suite at commit `76eefd0e53da2243d1e2ab45776db7761f4366ee`: 12/12 passed on Windows Python 3.11.9 in 0.003 s. The current log, Python environment, main commit, source Git blobs/SHA-256 values, and the 12 exact-main modules needed to complete this sparse checkout are retained in this package. Two earlier import-closure setup failures are preserved as `current_main_regression.log` and `current_main_regression_retry01.log`; neither reached a test case.

The corrected auditor verifies the baseline/provenance, the complete 12-test current-main log and source pins, and returns `AUDIT_HOLD_HISTORICAL_LOG_MISSING_CURRENT_MAIN_REGRESSION_PASS`. This validates the current deterministic recovery regression while keeping the original raw-custody limitation visible. It does not establish live writer ordering, physical input/release, useful feedback, MAP01 task outcome, or #59 completion.

The packaged import overlay was replayed once after staging, again yielding 12/12; its raw output is `package_overlay_replay.log` and is covered by the updated manifest.

Auditor hardening: every gate now uses explicit runtime checks instead of `assert`, so optimization cannot disable validation. `py_compile`, normal audit, and `python -O` audit pass; both audit modes return the same explicit historical-log HOLD.
