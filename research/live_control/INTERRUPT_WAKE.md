# Cooperative interruption wake and completion checks

The preceding live episode exposed 1121.361052 ms between verified key release and
terminal delivery inside the runtime. The old hold loop kept capturing and marked
the interrupted hold step complete. New explicit candidates address that behavior:

- `lease_cause_v2.py` wakes waits when an owner interruption is recorded or the
  lease cancellation method is invoked. Checkpoints raise DecisionRequired for
  focus/surface changes, Expired for recorded expiry, and Cancelled for recorded
  cancellation/stop. First recorded cause remains per-lease evidence.
- `executor_v5.py` checks the lease after each backend operation before counting
  the step complete and after final release before allowing completed status.
  Existing failed cleanup remains failed. A cause recorded during final release
  can change terminal status after earlier completed steps; this is not rollback.
- `decision_receipt_v3.py` adds attention whenever a terminal contains a non-null
  interruption or decision reason, even when its status says completed. This is
  an offline candidate, not the receipt used during the live episode below.

Old measured files/defaults remain unchanged. Capture, X calls and logging are not
preemptible. Event wake is cooperative and scheduler-dependent, not hard real-time.
Callers should use Lease.set(); direct writes to the inherited cancellation Event
do not themselves signal the new wake Event. Owner-recorded cancellation does.

## Evidence

`probe_interrupt_wake_v1.py` passed nine controlled cases: five recorded reasons
during a 500 ms wait, interruption before an unchecked backend return, interruption
during cleanup, normal completion, and explicit cancellation. It checks status,
completed-step accounting, first-cause presence and same-deadline lease isolation.
These use synthetic owner records; they do not establish X11 pointer behavior.
`results/interrupt-wake-01/report.json` retains events and source hashes.

One actual Inkscape episode (`cause-live-02`, seed 208) used the new executor/lease
with the same cause_session_v1 and owner10. The assistant viewed the initial image
and submitted a single one-second Control_L hold. The private injector verified
the key down, moved focus, verified it up, and restored focus. The terminal was
needs_decision, decision_reason focus_changed, with **zero completed steps**.
Verified release to terminal was **22.968832 ms**, with no intervening observations.

The fast interruption had no new image. The assistant explicitly requested an
observe-only program, reviewed its original image, and issued a new move/save
program. Saved SVG independently passed x=52, y=50, width=40, height=30, no transform.
The observation and recovery terminals had no inherited interruption. All selected
images and compact receipts were visible. The bridge handle returned exit 0.

`audit_cause_live_v2.py` verifies source pins, owner-to-receipt cause equality,
47 raw/received events without gaps or overlaps, and nine exact decoded frames.
Eight socket exchanges were needed, including the additional observation's clock
and submit. Initial capture to independent evaluation was **87.93470372 seconds**,
including model review, commentary, and preparation of the explicit recovery
helper. That helper is pinned before each stage, but was written after interruption;
its added preparation time is retained. No end-to-end speedup is claimed. The
preceding episode had a different program (a tail step), seed, and scheduling;
the two release-to-terminal numbers are observations, not a controlled effect size.

`probe_receipt_cause_v1.py` preserves internally consistent terminal copies in a
completed recorded report while injecting a cause or decision reason. Both gain
attention; the normal report remains unchanged in that respect. This checks a
specific presentation blind spot, not comprehensive schema validation or a live
completed-with-cause execution. Evidence: `results/receipt-cause-01/report.json`.

## Remaining work

Test the cooperative wake through actual pointer holds/drags and a finite matched
old/new sequence before attributing a latency gain. Check races at normal release,
capture in progress, and cancellation. Evaluate whether an explicit post-stop
observation can reduce recovery round trips without delaying the urgent terminal
or granting input authority. Keep no-image results explicit. Model identity,
actual model tokens/cost, receipt time, independent child-process cleanup inventory,
human-speed qualification and overall Research Freeze remain unverified.
