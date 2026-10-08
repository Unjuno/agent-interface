# Current-v39 per-key release telemetry — no-model X11 validation

Allocation: `MAP01-V39-RELEASE-TELEMETRY-LIVE-59-T0-20261004-01`.

## H / T / D / C / U

- **H:** The backend selected by `session_map01_v12.py` can emit identity-bound
  per-key explicit-up receipts for a real X11 single-key hold and a two-key
  hold. In each batch, all key-up calls finish before one owner-state sample
  and before telemetry publication; an independent XQueryKeymap observer sees
  each tested key down during the hold and up after terminal cleanup.
- **T:** In the task-owned isolated OrbStack Ubuntu/arm64 guest, instantiate the current v39
  session backend and its current executor with the real InputOwner v10 wrapped
  by `input_transition_owner_v3`. Run one 600 ms `space` hold, then one 600 ms
  `Up`+`space` hold on a fresh Xvfb/Openbox display. No model/provider, game,
  task scoring, user desktop, or network is used. Capture candidate events and independent 32-byte
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

Docker preflight could pull the pinned base but could not start a build step:
the OrbStack LXC guest denies `bpf_prog_query(BPF_CGROUP_DEVICE)`. The selected
route is the same task-owned isolated VM directly, with `unshare -n` for both
candidate and auditor, rather than claiming a container run. The freeze binds
the full guest and Python package receipt, current `main`, the v39 runtime
entry and dependency tree, this runner/auditor, source-support archive, input
program, output root, commands, and the one-candidate/one-auditor stopping
rule before candidate invocation. A failed/STOP candidate is retained as the
first outcome and is not retried.

## Frozen allocation outcome

Allocation MAP01-V39-RELEASE-TELEMETRY-LIVE-59-T0-20261004-01 invoked one
candidate. It exited 1 during the frozen network precondition because a
malformed line continuation applied unary + to a string. The failure occurred
before Session() creation, so no X server process or input action started. The
exact traceback and source hash are in results/<allocation-id>/. The harness
was repaired afterward and construction tests pass, but the frozen allocation
is STOP; its candidate is not rerun and the raw-only auditor is not invoked
after the nonzero candidate exit. No live telemetry or task-effect claim
follows from this outcome.
