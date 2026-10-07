# MAP01 v39 Xvfb per-key release identity A01

Issue #59. This is an isolated Xvfb construction experiment of the current
retained-input wrapper's real InputOwner/X11 path. It is not a game run or a
formal live allocation.

## H / T / D / C / U

**H.** The exact `doom_retained_input_backend_v4.py` source from PR #7717 head
`4781ae734dc90539e8e0e99a072e97a9932223cc`, paired with the frozen current-main
`input_transition_owner_v3.py` and `input_owner_v10.py`, will emit unique
admission identities and per-key release receipts that match actual Xvfb
KeyPress/KeyRelease events delivered to one focused client. Repeated same-key
cycles and reverse-order release of a two-key hold are included.

**T.** Start one private Xvfb server and one client window. In one executor step,
run ten repetitions of the frozen eight-edge sequence: `a down/up`, a second
`a down/up`, then `a down`, `space down`, `space up`, `a up`. Record every
requested edge, server keymap state after the owner call, client-dispatched key
event, admission receipt, and release receipt. Close the owner and retain the
first candidate outcome. Then run the raw-only auditor once.

**D.** `PASS_METHOD_SCOPED` requires exactly 40 admissions, 40 releases, and 80
client-dispatched events; monotonically assigned unique positions; exact
per-key `(id, step, admission_position)` matches on all release rows; the
expected false/true transitions in server keymap state; the expected client
event order for every sequence; verified empty owner state after each release
batch and at close; stopped Xvfb; and no audit mismatch. Any completed evidence
mismatch is `FAIL`; missing Xvfb, Xlib, focus, or complete cleanup evidence is
`STOP`. No candidate retry is allowed.

**C.** The backend's production `raw()` method, InputOwner v3/v10, XTEST event
routing, server keymap, and one X client are exercised. A small executor shim
calls the exact backend method to isolate this boundary; production observation,
planner, controller wait, Doom/ViZDoom, and game-time behavior are not exercised.

**U.** One private Xvfb guest and one sequence establish only local X server and
client dispatch for this source snapshot. This does not establish physical
keyboard state, Doom/application behavior, threat reaction, useful task
feedback, bounded live recovery, MAP01 progress, safety, or human tempo.
