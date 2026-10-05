# A02 plan: Xlib 0.33 list-return compatibility repair

Issue: #59; successor to A01 STOP in this package, not a retry of A01.

## H / T / D / C / U

- **H:** With a candidate that normalizes Python-Xlib 0.33's `query_keymap()`
  list of octets to bytes, a one-owner control and two independent V4/V3/V12
  owners on one private Xvfb display will show that owner A's key-up can make
  the server-global keymap neutral while owner B's local `held` map still
  contains W; both owners may then emit receipts marked verified.
- **T:** One candidate invocation using the exact PR #7974 head frozen in
  A02/FREEZE.json. Repeat the A01 control/pair sequence on a fresh `:98` Xvfb
  server. The only candidate-code change from A01 is converting the returned
  Xlib keymap sequence with `bytes(...)` before length/bit/hex operations.
- **D:** Apply the unchanged criteria from A01: control false/true/false;
  pair false/true/true/false/false; distinct owner and lease identities; A's
  key-up verified while B locally still owns the key; B's key-up verified;
  final keymap neutral; no cleanup errors. Preserve STOP or mismatch without
  retry. A confirmed result is an isolation failure for a shared display, not
  a success of the runtime.
- **C:** A01 stopped before calling down because Python-Xlib returns a list,
  not bytes. A02 measures the same X-server behavior after that test-harness
  incompatibility is repaired; it is versioned separately and its A01
  failure remains immutable.
- **U:** Private Xvfb server bookkeeping only. It says nothing about physical
  state, application/game receipt, production isolation policy, or the live
  threat-control requirement.

## Frozen source change

Only keymap representation normalization and A02 labels/output paths differ
from A01. Candidate, auditor and runner are separately hashed in A02/FREEZE.json.
