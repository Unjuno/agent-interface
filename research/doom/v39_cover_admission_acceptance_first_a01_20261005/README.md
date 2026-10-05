# V39 admission accept-first boundary A01

This construction test checks the accept-first FIFO ordering against current main (`c1074c4`) and the exact PR #7589 head (`763ff69`). The PR was based on older main (`6398060`), so both controller and wait-test snapshots are pinned separately. The event order is matching `accepted` first, then a hard-health observation before `begin_model_turn`.

H: Under that fixed FIFO, current main and the frozen #7589 proposal both return `accepted`; the caller begins the planner before its next monitored wait consumes the hard observation.

T: Execute the frozen production wait closure from each retained test source with `[accepted, hard observation]` (and the PR helper on its branch), then independently verify the raw event order, boundary snapshot, and source call order.

D: FAIL if planner start precedes hard-event observation; PASS if the event is consumed and planner start is suppressed; HOLD on a source/hash mismatch.

C: The caller may intentionally allow the already-admitted model turn to begin and rely on interrupt on the next monitor poll; that policy would require a bounded reaction guarantee not measured here. Other threads or instrumentation may observe events outside this synchronous wait path.

U: No timing, thread scheduling, cover execution, model, game, application effect, input, or live allocation is represented. This result does not establish threat damage, stale action execution, or user-visible harm.

Candidate/auditor v1 sampled `latest()` too late and mislabeled it; v3 had no prior observation in its extracted wait closure. Those attempts and corrections are preserved in `CORRECTION.md` and `CORRECTION_v3.md`. Candidate v4 seeds the prior neutral observation and runs both current main and PR #7589 using their pinned production wait functions and independent source snapshots.

Result: current-main wait tests pass 7/7, PR-head wait tests pass 8/8, the seeded accept-first candidate reproduces on both sources, and the independent v4 raw/source audit passes 35 checks with five corruption controls passing. In both cases, the planner input is prepared from the prior observation (sequence 8) and the planner turn starts before the next monitor-enabled wait consumes the queued hard-health observation (sequence 9). The monitor then sees the event and the source path interrupts/discards the planner result. This identifies a planner-start/reaction gap for the fixed queue ordering; it does not measure interruption latency, actual model use, task effect, or input authority. PR #7589's pre-accept monitor alone does not close this ordering.

The exact PR #7589 head and current-main controller snapshot are included for provenance. Run from this directory:

```powershell
$env:V39_WAIT_SOURCE = (Join-Path $PWD 'controller_main_c107.py'); python -B -m unittest wait_test_main_c107.py -v
$env:V39_WAIT_SOURCE = (Join-Path $PWD 'controller_pr7589.py'); python -B -m unittest wait_test_pr7589.py -v
python -B candidate_v4.py
python -B audit_v4.py
python -B -m unittest test_audit_v4.py -v
```

The first two commands cover the existing wait tests. The candidate is an in-memory FIFO construction, not a live allocation. `audit_v4.py` independently checks source SHA-256/Git blob identities, both event traces, the seeded prior-observation boundary, data-flow/source order, and auditor wiring; it does not import the candidate. The final command runs auditor corruption controls. v1–v3 artifacts are preserved earlier attempts; v4 is the corrected comparative result.
