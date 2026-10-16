# Observation horizon after Tk event processing — Issue #2279

Intake main: e4c2e58122aa138e421048d8e86ec18259143b9e.
Additive publication path: research/live_control/tk_observation_horizon_2279_v1/.
Branch: research/tk-observation-horizon-2279-20260922.
Allocation: tk-observation-horizon-2279-20260922-01.

## Question / lineage

The exact main experiments/x11_dwell_unknown_preflight_2279.py is Git blob
f60bd81d37f574337d8aebb9a02fe35b12ab26fd. Its README defines COMPLETED as a
fixture effect observed before the horizon. Its loop checks time before
root.update(), which processes callbacks, and does not recheck time before
reporting completion. This bounded engineering/scientific validation stays
under the existing #2279 question. No wrapper-successor Issue is required.
Old preflight results and analytical #1895/#2402 are not rerun or overwritten.

#4000 already owns retrospective publication of our earlier 12-case pause
study, so that study is not duplicated. The conversation-local 24-case X11
coalescing study remains HOLD_EXTERNAL_EXIT_UNOBSERVED; its complete supplied
ZIP SHA256 is 4c3d4cb9817c1bf20c9e93cab08335825766da94c4ba0dacb808bc979d3275ee.
No previous measurement is repeated or promoted by this allocation.
Parallel capture-age #4010 and timerfd #4001 operate different boundaries.

## H / T / D / C / U

H: a GUI callback that returns after the observation horizon can cause the
pinned precheck-only loop to report COMPLETED for a late observation. Sampling
the clock after reading the widget, before assigning completion, prevents
that false within-horizon label without erasing the actual late effect.

T: supplied Linux x86_64 execution container, CPython 3.13.5, Tcl/Tk 8.6.16,
private authenticated Xvfb (TCP disabled), no inherited display. Six scenarios:
fast 50/200 ms; delayed 350/200 ms; absent none/200 ms; late 350/500 ms;
blocked_fast 50/200 ms plus a real 300 ms callback; blocked_absent none/200 ms
plus the same callback. Two policies, two fresh repetitions = 24 new worker
processes. Two immutable 12-case batches, repetition 0 original/repaired order,
repetition 1 repaired/original order. Each creates/destroys its own Tk root.

Use a copy of the full pinned source. AST replaces only the CASES allocation;
a passive record_start call is inserted; the candidate replaces exactly two
completion-assignment lines. Both arms use identical observation wrappers.
The blocking callback is scheduled at the second root.update call, after the
loop's time check. Real Tk callbacks mutate/read the label. This is not raw
screen capture, independent physical-effect measurement, the production CLI,
or the original four-case historical allocation. The legacy summary field
unsafe_timeout_as_completion merely counts UNKNOWN; it is not used as a safety
metric here. The proceeded Boolean never executes an input operation.

One excluded 12-case construction block and three source/strict-boundary tests
passed; the read-only auditor rejected nine corrupted evidence copies. No
formal case has run. Freeze sources, environment, effective AST hashes and
this plan publicly before formal batch 0. Per-worker deadline 4 s; each batch
gets a 30 s external process timeout and a 40 s tool envelope. The actual batch
exit is saved by the shell. Require successful complete batch 0 before batch 1.
Existing output paths are refused; no retry/replacement/exclusion/tuning.
Preserve any STOP under this Issue, without creating another wrapper question.

D: PASS_OBSERVATION_HORIZON_BOUNDARY_SCOPED only if all 24 exact cases/source/
process/cleanup records reconstruct; original four scenario outcomes agree
in both arms; both blocked_fast originals report late COMPLETED, both repaired
ones retain the late effect but report UNKNOWN; blocked_absent stays UNKNOWN;
no repaired COMPLETED has observed_at >= horizon; both Xvfb and all worker/
external batch exits are observed zero; the separate raw-only auditor and nine
corruption controls pass. Complete scientific disagreement is FAIL; missing
source/rows/exits, timeout or ambiguous evidence is STOP/HOLD, not PASS.

C: callback delay is explicit fault injection, not natural scheduler incidence.
This is a reproducible discrepancy with the fixture README's observation-time
contract, not a Tcl/Python defect, a production-runtime vulnerability, or a
rejection of all prior preflight evidence. A post-observation gate does not
interrupt root.update and therefore does not enforce a hard return deadline.
UNKNOWN does not mean no effect, cancellation, or permission to retry.

U: no model/provider/network experiment, GUI input, user documents, production
runtime edits, natural event rates, latency saving, calibration, hard-real-time,
or end-to-end task result. Docker/gh CLIs and engine/image identity unavailable
in this worker environment, not a fleet-wide statement. Independent audit is
a different implementation/process by the same author, not external review.

## Conditional derivation / variable table

| Symbol | Meaning | SI unit | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| t0 | monotonic start | s | recorded start | one process clock | scalar real |
| h | observation horizon | s | scenario 0.2 or 0.5 | strictly positive | scalar real |
| tc | pre-update clock check | s | loop entry clock | tc >= t0 | scalar real |
| to | post-widget observation clock | s | recorded observed_at + t0 | to >= tc | scalar real |
| d | observed elapsed time | s | to - t0 | nonnegative | scalar real |

The original condition is tc - t0 < h. It does not imply to - t0 < h because
root.update may execute a callback between tc and to. For example t0=0,
tc=0.001, h=0.2 and to=0.301 satisfy the first condition but not the second.
The repaired assignment defines COMPLETED only if d < h, using the same d that
is returned as observed_at. Thus every repaired COMPLETED has its recorded
observation inside the declared horizon; d=h is UNKNOWN. Both sides of each
comparison have units seconds. This proves only a recorded observation-time
invariant, not termination by h or an effect's causal completion timestamp.
Actual callback/read brackets are additionally retained and checked.

## Roadmap / reproduction boundary

Intake and collision checks -> excluded construction -> public source freeze
-> two one-shot batches -> separate raw-only audit/corruptions -> additive PR
-> exact-head checks/review -> main readback if qualified -> own branch cleanup
only after ownership/dependency checks. #2279's two-family calibration, model
uncertainty use and task-benefit criteria and the full ROADMAP remain open.

Primary semantics: Tcl 8.6 after/update manual and Python tkinter threading
model. Event-loop processing is not a deadline guarantee. Official references:
https://www.tcl-lang.org/man/tcl8.6/TclCmd/after.htm
https://www.tcl-lang.org/man/tcl8.6/TclCmd/update.htm
https://docs.python.org/3.13/library/tkinter.html
