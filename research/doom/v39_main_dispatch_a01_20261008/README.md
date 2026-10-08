# V39 main-loop dispatch boundary probe

This construction-only experiment tests whether the actual V39 `main()` queue-consumer closure carries the full observation paired with a typed hard-invalidation event through the real cancel helper, and whether source refresh selects that full observation for the next planner turn.

## H/T/D/C/U

**H — Hypothesis.** When a health sequence crosses the admitted cover floor while a model turn is pending, V39's `wait()` returns a policy invalidation on the typed event. The subsequent `cancel_invalidated_cover()` call waits without an observation monitor, so it should consume the paired full observation, update `latest`, wait for a verified empty-release terminal, reject the stale planner answer, and leave a fresh source for the next turn.

**T — Test.** Execute the exact AST-extracted `wait()` closure and exact production `DoomCoverSignalPairMonitor`, `cancel_invalidated_cover`, and `doom_source_refresh_v1.refresh_source` functions against an inert queue, fake process/planner, and synthetic paired health/ammo epochs. Sequence 10 begins at health 70/ammo 8; sequence 11 crosses the health floor at 60. Enqueue the typed invalidation first, then its full observation and the matching neutral terminal. No Doom process, model, App Server, GUI, or OS input is started.

**D — Decision.** PASS requires typed invalidation to escape the main wait; executor cancel write/flush before planner interruption; completed stale answer marked ineligible; the cancel wait to consume the full sequence-11 observation and verified-empty terminal; and source refresh to return that observation. Any lost/stale source, reordered cancel, admitted answer, or unverified release is FAIL.

**C — Competing explanation.** This deterministic harness does not reproduce producer scheduling or timing. It tests dispatch and composition at the existing main-loop closures, while the image and observations are synthetic. It cannot establish live invalidation latency or whether a real model-authored policy is useful.

**U — Limits.** This is an offline main-loop boundary check only. It does not show input reached an application, physical release, useful feedback, recovery, damage reduction, survival, or MAP01 completion. The stale-answer object is an inert fake in this test; the adjacent #8478 probe separately exercised the exact planner adapter. Issue #59's live threat exposure remains open.

## Result

One case passed normally and under `python -O`. The actual main wait returned the sequence-11 hard invalidation. The cancellation helper flushed cancel before planner interruption, then consumed the paired full observation while waiting for the terminal. The actual source-refresh function returned sequence 11 with status `already_observed`. The terminal carried `verified: true`, empty keys and buttons. This confirms this queue-consumer composition only.

Two fault-injection controls were run in a disposable repository copy: removing `wait()`'s update of `latest` made the test fail because the fresh observation was lost; removing the `before_transport` cancel callback made the test fail at the cancellation boundary. Both expected failures were caught. The disposable mutation copy is outside this package and does not modify the pinned checkout.

`FREEZE.json` pins the main commit and source Git blobs. `audit_probe.py` checks those pins and the retained run exit/output hashes. Raw process outputs and exit codes are retained here. The package does not rewrite an existing result bundle when the test is rerun.

## Reproduction

From this directory:

```powershell
python test_main_dispatch.py
python -O test_main_dispatch.py
python audit_probe.py
```
