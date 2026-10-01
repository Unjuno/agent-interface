# Issue #3633 — v4 filtered identity + readiness gate

## Scope

One fresh Docker/OrbStack allocation tests whether the v4 X11 application
identity filters produce a stable, typed, unique Inkscape/LibreOffice Calc/
Chromium identity set that the repository's `mixed_app_identity_2666` gate
admits before any geometry, focus, transition, or input operation. This is a
readiness rung only; it does not run the #2499 long-session schedule.

## H/T/D/C/U

- **H:** The v4 filtered resolver plus the main-branch typed readiness gate
  will admit exactly one stable identity per required app on the same private
  X11 display, and fail closed for missing, ambiguous, unstable, duplicate,
  wrong-display, and malformed identities before any geometry/input operation.
- **T:** Freeze main SHA, resolver/gate/test sources, image ID, app filters,
  timeout, and output path. In one network-disabled, read-only-root container,
  start private Xvfb and the three apps, collect two consecutive complete
  visible-window snapshots, apply the v4 app-specific filters, and call the
  existing typed gate. Run deterministic adversarial gate unit controls in
  that same pinned image. Retain all candidate properties and process cleanup.
  Run a separate read-only-source auditor against the retained output.
- **D:** `PASS_READINESS_IDENTITY_V4_SCOPED` only if the three live apps each
  yield one stable distinct identity, the typed gate admits them, all negative
  unit controls refuse for the expected reason, no geometry/focus/input/model/
  network operation occurs, processes are reaped, and independent audit passes.
  Any bounded startup/identity miss is `STOP_READINESS_IDENTITY_UNAVAILABLE`;
  an accepted malformed/ambiguous identity or any forbidden operation is FAIL.
- **C:** Uses issue #3633's v4 filtered identity/readiness prerequisite and
  current main `identity_gate.py`. Does not alter #2499, #2937, the prior
  long-session failures, or fixture PASS evidence. One formal allocation,
  no retries; no geometry/focus/transition/input.
- **U:** This does not establish geometry, focus recovery, stale capability
  admission, task effects, the four-transition long session, model benefit,
  broad app reliability, or production readiness. If this gate passes, #3633's
  separately frozen persistent-session allocation remains necessary.

## Frozen allocation

- Allocation ID: `issue3633-readiness-identity-v4-formal-01`
- Source base: `5db7858067bda50590674370f494230f2a5dd6d9`
- Container image: `mixed-app-identity-2782-local:latest`,
  `sha256:e6ced3789130dae21c7b42b7b9d25cd590a271a77910e16c01d2edf87e44cee6`,
  Linux/arm64. Network disabled; root and source read-only; only `/evidence`
  is writable; `/tmp` is bounded tmpfs.
- Run exactly once. Construction observations and formal readiness rows are
  retained together but distinctly tagged; do not rerun/tune in this allocation.

Exact output and SHA-256 manifest are retained beside this file under
`evidence/formal-01/`.
