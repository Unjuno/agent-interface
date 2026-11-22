# MAP01 V39 cancellation-cleanup telemetry bridge A01

This one-shot fake-display construction composes the V13 cancellation-cleanup
owner from draft PR #7769 with the V39 per-key bridge on main and the exact
`input_edge_receipts` projector from the then-current #7602 head. The experiment
addresses a concrete #59 instrumentation question: does a verified asynchronous
owner-thread key release reach the program/step telemetry used by the projector?

## H / T / D / C / U

- **H:** A cancellation cleanup may release a held key after the caller's
  `down` returns but before its sequential `up` call. If the bridge forwards
  only synchronous call results, the owner can verify release while the
  projector has no per-key up interval.
- **T:** One F8 down through the frozen V39 `Backend.raw`; cancel the lease;
  retain the V13 owner cleanup record on its fake display; issue the later F8
  up through the same bridge; project only the rows the bridge actually emits.
- **D:** The independent raw audit reports `PASS_GAP_REPRODUCED` only if cleanup
  verifies neutral fake-display state and a `CONFIRMED_PHYSICAL_UP` bracket for
  the down actuation, while the bridge's later up is `NOOP_ALREADY_UP` with no
  adapter edge and the projector has no paired up interval. Identity, authority,
  effect, and projector-interval mutations must be rejected.
- **C:** This isolates an event-propagation/schema gap in a fake-display
  construction. It says nothing about whether a live V39 run actually reaches
  this cancellation interleaving or whether the game benefits.
- **U:** One key, one cancellation, host Python and a fake display. No live GUI,
  OS input, game, model call, application effect, recovery benefit, threat
  response, or MAP01 progress was observed.

## Result

The frozen V13 owner reported a verified `CONFIRMED_PHYSICAL_UP` for the same
actuation as the admitted down and left the fake display neutral. The V39 bridge
emitted the admission plus a later `NOOP_ALREADY_UP` measurement with no
actuation ID or adapter edge. The #7602 projector returned two incomplete
receipts with null up intervals; it did not pair the physical cleanup result.
The raw-only audit and three corruption controls pass.

A separately labeled post-hoc schema control shows that the retained cleanup
measurement can produce a paired receipt when wrapped with the original
program/step identity and an adapter-edge projection derived from its bracket.
Without that adapter-edge projection it remains incomplete. This control was
not emitted by the candidate bridge and is not runtime integration evidence.
It narrows the integration requirement to forwarding cleanup with the original
context and serializing the measured edge into the projector's expected schema.

## Boundary against the separate release-receipt path

Current #59 evidence in draft PR #7769 A08 source-composes the retained cleanup
through V39 lease interruption, executor publication, controller handoff and
the `RunningActionGuardV3` release receipt. Its audit reports both per-key
brackets and actuation IDs preserved, and the frozen controller/lease/executor/
guard sources were byte-identical on main `a9352dc53c783f1501046d762bc36c34bc6ab480`.
That is a distinct telemetry path. This A01 result does **not** claim that all
V39 release receipts lose cleanup evidence; it is scoped to the opt-in #7602
adapter-edge projection that consumes only `input_admission` and
`input_release_measurement` rows.

The retained A01 raw was read-only reprojected with the later #7602 head
`c81512edfbb9dba5f9db8127884683b0500acf4f`; the supplemental
`CURRENT_PROJECTOR_RECHECK.json` still has two incomplete receipts and no up
interval. The candidate was not rerun.

Candidate output was retained as initially written, with its status
`PENDING_INDEPENDENT_AUDIT`; the auditor's scoped disposition is in
`results/a01/AUDIT.json`. The candidate process exited 0. Its wall-clock start
and finish were not captured; retained monotonic sample brackets are not a
substitute for those missing timestamps. No container was used because this
was a bounded Python fake-display harness without a GUI or OS-input boundary.

## Provenance and reproduction

`FREEZE.json` binds main `8c45935e065ec36f8d42b7d4e59224900d5a83d2`, V13 source
from PR #7769 head `0525b97350568f85d23d0c214f3bb83c376ae2f4`, the V39 bridge
source from main, the `input_edge_receipts` projector from PR #7602 head
`5cbaa4fb2c08f4cf968e81f5fbbcd51aa939760b`, the fake-display harness, Python
version and source hashes. The exact extracted-function hashes are recorded in
the freeze.

The no-retry candidate invocation has been consumed. Do not rerun it or replace
`results/a01`. To reproduce the retained audit and schema-only post-hoc control,
run from this directory:

```sh
python3 audit.py
python3 -m py_compile run_candidate.py audit.py
git diff --check
```

The experiment informs the #59 telemetry prerequisite only. It does not supply
the separately unassigned live threat-exposure allocation or satisfy Issue #59.

## A02 read-only audit successor

Review of A01 found that its original auditor checked the cleanup interval
against sample finish timestamps but did not verify sample availability, sample
errors, the observed down-to-up state transition, sample start/finish order, or
the release-request/XSync timing inside the sample bracket. A raw mutation
setting both samples unavailable and reversing their states still passed A01's
`audit_raw` as `PASS_GAP_REPRODUCED`. This is an audit weakness; the original
A01 raw and result are unchanged.

A02 adds a separate raw-only audit over the exact retained A01 bytes. It passes
`PASS_AUDITED_GAP_REPRODUCED` after verifying both admitted-down and cancellation-up
sample state transitions, successful samples, ordered sample intervals, and
press/release request plus sync returns inside their brackets. Fourteen mutation
controls reject unavailable/error samples, state reversals, sample/timing
corruption, actuation mismatch, authority, and application-effect claims.
Candidate invocations remain zero; no fake-display run, GUI, OS input, game, or
model was repeated.

- **H:** An independent raw-only audit can confirm A01's cancellation bracket
  while rejecting malformed sample, state, identity, authority, effect, and
  timing evidence.
- **T:** Replay the exact retained A01 raw through A02 once, then run fourteen
  in-memory corruption controls. Do not invoke the candidate.
- **D:** PASS only if both retained brackets reconstruct and every corruption
  control is rejected.
- **C:** A01's candidate raw may be valid despite the weaker original audit;
  A02 strengthens audit coverage without changing A01's result.
- **U:** One key and one fake-display cancellation trace. No live OS input,
  useful feedback, recovery, application effect, or MAP01 progress.

Reproduce from this directory with:

```powershell
python build_freeze_a02.py
python -m py_compile audit_a02.py test_a02.py build_freeze_a02.py
python -m unittest -v test_a02.py
python -O -m unittest -v test_a02.py
python audit_a02.py
```

The A02 freeze binds the A01 raw, A01 freeze, A01 audit source, A02 auditor,
tests, and freeze builder. The local `.gitattributes` keeps A02 code/results in
LF and preserves the frozen A01 source bytes exactly across checkouts. A02's
result is a stronger audit of the same single-key fake-display trace, not new
runtime or scientific evidence.
