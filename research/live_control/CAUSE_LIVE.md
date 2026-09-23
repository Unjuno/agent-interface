# Cause delivery through a live application and compact receipt

One fresh Inkscape episode, seed 207, used explicit candidate entrypoints
`cause_socket_entry_v1.py` and `cause_interactive_v1.py`. `cause_session_v1.py`
preserves session_v9 operations while selecting input_owner_v10; executor_v4
selects the per-intent cause lease. This is a different runtime from the frozen
owner5/executor3 comparisons, not a paired performance measurement. Defaults and
previous evidence remain unchanged.

The assistant viewed the original initial image, then submitted a one-second
Control_L hold followed by a Right hold. A separate X connection in the private
fixture observed Control_L physically down, transferred focus to a temporary sink,
verified the key was up, restored focus, and destroyed the sink. This is an
injected fault, not a naturally occurring failure-rate sample.

The received compact receipt displayed needs_decision, the unique intent token,
the original verified focus_changed release, and the separate final cleanup
release. The assistant read the terminal and step/admission details and viewed
the selected image. Only Control_L was admitted; the Right tail was not admitted.
An explicit new program selected the rectangle, moved it right and saved. Its
terminal completed four steps with no inherited cause. The assistant viewed the
final image and requested independent evaluation: saved SVG x=52, y=50, width=40,
height=30, no transform. Both receipts and all three selected images were visible;
no full-report review or verified model receipt timestamp is claimed.

## Important failure retained: notification remains late

Physical release did not stop the ongoing hold's observation loop. It continued
for 11 captures after release and marked that hold step completed. The next step
then detected revoked focus authority and returned needs_decision. The interval
from verified owner release to terminal was **1121.361052 ms**. This is local
runtime timing, not model latency or a hard real-time guarantee.

This is more than a logging issue: a program ending at the hold could reach its
normal completion path while containing an interruption. That single-step case
was not executed here. The observed step completion and current checkpoint code
justify testing it next. The compact receipt currently surfaces non-completed
terminals but does not separately flag a completed terminal with a non-null cause;
its full terminal is visible, yet automatic attention needs explicit coverage.

Next implement cooperative interruption notification that wakes bounded waits and
is checked before declaring steps/programs complete. Preserve distinct focus,
expiry and cancellation meanings; ordinary cleanup must not create an interruption.
Test interrupted single-step holds and pointer waits, normal operation, and new
intent isolation, then repeat a fresh app episode. Do not simply add more polling
captures, turn interruption into success, or infer a speedup from source changes.

## Evidence and limits

`results/cause-live-01/` retains source pins, original reports, raw socket replies,
receipts, injection evidence, SVG and frame artifacts. `audit_cause_live_v1.py`
verified all recorded source pins, exact owner→terminal→socket→receipt cause
equality, all 52 received events against the runtime log with no overlaps/gaps,
and all 19 decoded frames against their PNGs. Six socket exchanges were used.
Receipt JSON sizes were 4193 and 3967 bytes; these are not token counts.

Initial capture to independent evaluation was 63.802470376 seconds, including
assistant inspection and commentary. Bridge process exit was 0, observed via its
live process handle after finish. The inherited fixture has no independent
per-child cleanup inventory. Model identity/configuration, actual model tokens,
cost and model receipt times remain unavailable. This episode establishes
integration and exposes a concrete feedback delay; it does not establish human
speed, general performance, Research Freeze or formal benchmark adoption.
