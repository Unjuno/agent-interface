# Cleanup-overlap construction v1

Issue: #59, per-key admission/up/release attribution.

## H/T/D/C/U

- **H:** when the underlying `InputOwner` records a verified cleanup release
  inside an adapter's explicit `up` call bracket, the current-v39 backend may
  incorrectly retain `ordinary_release_candidate=true` and verify it as an
  ordinary release.
- **T:** exercise one explicit release receipt with a deterministic owner
  cleanup timestamp inside `[release_call_started_ns, release_call_returned_ns]`;
  compare an otherwise identical timestamp outside the bracket; remove the
  cleanup log as a fail-closed boundary.
- **D:** timestamp inside bracket must demote ordinary release and owner
  transition verification; historical cleanup outside the bracket must leave
  the ordinary release positive; missing owner records must refuse verification.
- **C:** current-v39 `doom_typed_release_backend_v3.Backend.raw` and buffered
  batch adjudication with an in-memory owner, through its actual adapter method.
  The baseline is the exact source at the PR #7378 head (`fbed929...`).
- **U:** this deterministic constructor tests telemetry classification only.
  It does not reproduce owner-thread queue scheduling, X11, a game, physical
  release timing, task effect, live MAP01, model use, performance, or safety.
  No gated/consumed allocation was invoked or retried.

## Frozen source and decision

Base PR head: `fbed929f629dabaa9ae752019d0ee7151d4d2298`.
Candidate source: `research/doom/doom_typed_release_backend_v3.py`.
Regression suite: `research/doom/test_doom_typed_release_backend_v3.py`.
Expected outcome: exact cleanup timestamp overlap is detected per row and
fails ordinary verification closed; no-overlap behavior remains positive.

