# Issue #59 T1 — autorepeat after focus transfer during a held key

## H / T / D / C / U

- **H:** On a private X11 server, moving focus while a key remains globally
  down does not necessarily stop its autorepeat stream from reaching the new
  focused window. If repeat is enabled, B may receive `KeyPress` repeats even
  though it never received the initiating `KeyPress`.
- **T:** In one fresh Xvfb, make two clients A and B select key events. First
  hold W on focused A long enough to observe at least two A `KeyPress` events
  while `XQueryKeymap` says W is down; release and confirm cleanup. Then press
  W on A, wait for its initiating `KeyPress`, move focus to B without releasing,
  and observe a fixed 1.2-second held interval before releasing. Record complete
  keymaps, exact focus IDs, action/receipt monotonic timestamps, all app key
  events, repeat-control state, and Xvfb cleanup. One candidate and one
  independently implemented raw-only auditor; zero retries.
- **D:** The experiment is interpretable only if the A positive control has at
  least two W `KeyPress` receipts during one down interval, W remains globally
  down throughout the B-focused interval, focus is confirmed on B, and the
  initial W press was received by A. `PASS_X11_HELD_REPEAT_REACHES_NEW_FOCUS`
  iff at least one W `KeyPress` is received by B after B becomes focus and
  before release. `FAIL_X11_HELD_REPEAT_NOT_OBSERVED_IN_BOUNDED_WINDOW` iff the
  positive control succeeds but B receives zero such presses in 1.2 seconds.
  Missing positive control, identity, timing, or cleanup is STOP, not FAIL.
- **C:** Successor to Issue #59 T0 app-delivery experiment at main
  `ab43adce8141182f6bcfa76df469854b1ae11116`. T0 observed zero B KeyPress in a
  50-ms immediate window, then a B KeyRelease without a recorded B KeyPress.
  This T1 specifically tests the longer held interval and server autorepeat;
  it does not duplicate the immediate focus-transfer observation.
- **U:** XTEST/Xvfb only, amd64 emulated by OrbStack on arm64. No physical input,
  real desktop, game, model, semantic app effect, threat response, MAP01
  progress/survival, latency generalization, safety, or efficacy claim. A
  received repeat is protocol delivery, not proof the app acted on it.

## Stop rule

Freeze image/source/fixture before one candidate invocation. Run one independent
raw-only audit, no retries. Retain candidate stdout/stderr and audit outputs.
An unavailable Xvfb repeat positive control is STOP because the distinguishing
stimulus was not established.
