# Primary two-editor use with explicit click delay

The primary assistant used the built public MCP runtime through the Windows-to-WSL
stdio relay to enter and save two different values in two visible ordinary Tk
windows: left `http://p_q`, right `http://s_t`. It chose pointer coordinates from
the initial image, inserted an explicit 50 ms delay after each click, reviewed
each unsaved value image, then issued a separate Ctrl+S program. It reviewed both
saved labels before closing. Independent files checked only after control ended
match both exact requested values.

Six MCP calls: initial observe, left input, left save, right input, right save,
close. Four input programs, five images and five attributed reviews. No missing
characters, repairs, extra observations, input replay or full-result retrieval
were needed. Both paced input replies used opt-in brief projection; save replies
remained full because the short nonpaced reports are not eligible. All four
programs report verified release and the persistent session closed normally.

This is a fresh primary functional example, separate from the twelve scripted
[matched comparison cases](../click-text-comparison-01/README.md). It does not
establish a general safe delay, fewer round trips, faster model interaction or
human parity. Value review before save intentionally retains a model decision
boundary. The caller requested 760 ms of fixed delays in total: two 50 ms
post-click waits, two 180 ms character-gap totals, two 50 ms input feedback waits
and two 100 ms post-save waits. These are not application acknowledgements.

The portable artifact was built from main
`5ef3cf2f1311f61ff96186da5a0003f5369b2dfa`; its full bytes and source manifest are
retained. Environment: Ubuntu WSL, private Xvfb/Openbox, JP keymap, two fixture
processes differing only in title and initial geometry. No helper model, new
sensor, clipboard insertion or application-state oracle selected the actions.
The fixture runner supplied target IDs and evaluated files after closure.

`host-timing.json` preserves host intervals and explicitly lists unmeasured
model-visible useful feedback, semantic completion, reasoning/wait time and
actual provider tokens/cost. No prior trial with different tasks is used as a
speed baseline. Review receipts establish attribution/order, not an automated
proof of what the primary understood; the conversation contains the actual images.

`raw.tar.gz` preserves images, requests/replies, reviews, host events, native
reports, fixture sources/events/effects, build and cleanup. Transport exit is 0;
all owned processes are terminal (Xvfb 0, Openbox 1 during teardown, fixtures
SIGTERM -15). Xlib emitted a missing-xauthority diagnostic at startup. These
statuses are not rewritten as uniformly clean zero exits.

Run `python3 -O runtime/results/click-primary-01/verify.py` to verify retained
bytes, exact requested/saved values, input-before-review-before-save ordering,
fixed delays, image identities, release and terminal outcomes. This read-only
verification sends no input and does not rerun the primary trial.
