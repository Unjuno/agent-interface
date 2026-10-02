# Issue #59 T0 — application-delivery boundary

## H / T / D / C / U

- **H:** A server-global X11 keymap bit being down does not by itself establish
  that the currently focused application received a corresponding KeyPress.
  With key W held on a private X server, moving focus from window A to window B
  should leave the W keymap bit down while B has received no W KeyPress.
- **T:** In one fresh private Xvfb, create two minimal client windows. First
  deliver one W down/up pair while A remains focused (positive control). Then
  focus A, press W, move focus to B without releasing W, sample the global
  keymap, then release. Record exact focus IDs, keycode, ordered XTEST actions,
  full 32-byte keymap samples, and application event receipts. Candidate runs
  exactly once; an independently implemented raw-only auditor runs exactly
  once; retries are zero. No model/game/desktop/physical input is used.
- **D:** `PASS_X11_APP_DELIVERY_BOUNDARY_SCOPED` only if the positive control
  has keymap false→true→false and A receives both KeyPress and KeyRelease; the
  focus-transfer case has the same key down before/after focus changes, B is
  the confirmed focus target, and B receives zero W KeyPress events before
  release. Any identity, ordering, bitmap, event, focus, or cleanup contradiction
  is FAIL/STOP. A pass demonstrates non-equivalence of global occupancy and
  current-app event delivery, not physical occupancy or task effect.
- **C:** Current source main `2b25814229e6b7072a7e28eeaa8870f4448354ae`.
  Predecessor #59 T3 (`map01_owner_occurrence_xvfb_59_t3_20261002`) proves only
  per-occurrence Xvfb `XQueryKeymap` witness construction using XTEST; it did
  not create application windows or measure event delivery. This allocation
  adds one positive-control pulse and one focus-transfer-in-held-interval
  contrast; it does not repeat T3's owner implementation test.
- **U:** Private virtual X server and synthetic XTEST only; Xvfb is not a real
  desktop or game. Window event receipt is not semantic/useful application
  effect. No physical keyboard, OS input authority, user GUI, model, game,
  MAP01, survival, progress, or performance claim. The frozen image is amd64
  under OrbStack on an arm64 host (emulated); timings are diagnostic and are
  not generalized to native host or physical input. Existing shared container
  `unjuno-native-ci-6092` is not used or modified.

## Formal stop rule

One candidate invocation, one independent audit invocation, zero retries.
Container start/command failure is recorded as infrastructure STOP and is not
interpreted as a scientific FAIL. Keep raw candidate output and audit output
immutable after the run.
