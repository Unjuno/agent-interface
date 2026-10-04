# Current-v39 per-key release telemetry — no-model X11 validation

Allocation: `MAP01-V39-RELEASE-TELEMETRY-LIVE-59-T0-20261004-01`.

## H / T / D / C / U

- **H:** The backend selected by `session_map01_v12.py` can emit identity-bound
  per-key explicit-up receipts for a real X11 single-key hold and a two-key
  hold. In each batch, all key-up calls finish before one owner-state sample
  and before telemetry publication; an independent XQueryKeymap observer sees
  each tested key down during the hold and up after terminal cleanup.
- **T:** On a fresh isolated Xvfb/Openbox display, instantiate the current v39
  session backend and its current executor with the real InputOwner v10 wrapped
  by `input_transition_owner_v3`. Run one 600 ms `space` hold, then one 600 ms
  `Up`+`space` hold. No model/provider, game, task scoring, user desktop, or
  network is used. Capture the candidate events and independent 32-byte
  XQueryKeymap snapshots; run one separate stdlib-only raw auditor afterward.
- **D:** `PASS_X11_TELEMETRY_ADAPTER_SCOPED` requires both candidate programs to
  complete; admission identity to match each expected key; every requested key
  observed down while held and up after terminal cleanup; release receipts to
  match intent token, owner, key, batch identity, count and position; monotonic
  release brackets to precede one empty-owner sample and subsequent publication;
  the Xvfb process and owner to close cleanly; and all frozen mutation controls
  to be rejected. Any source/resource/custody mismatch is STOP. Any missing or
  inconsistent telemetry is FAIL. This gate does not establish MAP01 task
  effect, application consumption, release-to-feedback latency, recovery
  efficacy, or safety rate.
- **C:** XQueryKeymap is a server-state snapshot. The fixed `space` and `Up`
  inputs are issued only to the private Xvfb session. A 600 ms hold is ample for
  observation but does not create a hard timing guarantee.
- **U:** One Linux/arm64 guest and one X server cannot establish cross-host
  timing or useful task feedback. The parser's separate timestamp-order defect
  is not resolved by this producer test; raw-only ordering checks are included
  here, and occupancy analysis remains gated on the independently reviewed
  parser repair.

The prospective freeze must bind current `main`, the v39 runtime entry and
dependency tree, this runner/auditor, the source-support archive, image digest,
input program, output root, commands, and the one-candidate/one-auditor stopping
rule before candidate invocation. A failed/STOP candidate is retained as the
first outcome and is not retried.
