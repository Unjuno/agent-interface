# Issue #5268 — Verification IR v0.1 first finite allocation

## H — hypothesis

A deliberately small typed Verification IR can represent the required checks
for this frozen 10-case Agent Action corpus without losing primitive identity,
subject, criticality, required evidence role, verifier class, dependencies,
deadline slot, budget class, or fallback. The representation itself creates no
authority. Unsupported requirements remain explicit as
`UNKNOWN_CHECK_REQUIRED`.

## T — frozen discriminator

Base commit: `6cd858858f0909cab5357de054404792a0148910` (current `main`).
Allocation: `verification-ir-5268-v01-20260930-01`.

One no-network Python process lowers 10 hand-authored action-state fixtures
through `candidate.py`, serializes/reparses each IR, and retains the complete
action/IR records. The fixtures cover baseline, target replacement, intent
scope change, expired decision deadline, revoked permission, already-satisfied
effect, target ambiguity, external side effect, unknown evidence, and optional
diagnostics. `oracle_expected.json` is a separately authored literal table.
`audit.py` imports no candidate, runner, fixture generator, or test module; it
compares every typed field and action against the frozen input and then applies
eight hand-authored corruptions.

Command (formal invocation exactly once):

```sh
python -I -S -B -c 'import sys,runpy; sys.path.insert(0,"/work"); runpy.run_path("/work/run_formal.py",run_name="__main__")'
python -I -S -B -c 'import sys,runpy; sys.path.insert(0,"/work"); runpy.run_path("/work/audit.py",run_name="__main__")'
```

First command must create `FORMAL-01.json`; runner refuses to overwrite it.
The second command is read-only. Unit/construction tests are separate from the
single formal invocation.

## D — decision

`PASS_IR_ORACLE_FINITE_SCOPED` only if all 10 plans exactly match the literal
oracle, all typed distinctions and dependencies survive JSON round-trip, zero
authority fields appear, unknown requirements remain marked, and all 8
corruption controls are rejected. Any mismatch is `FAIL_IR_CONTRACT`; a
missing/changed source or image identity is `STOP_PROVENANCE`; inability to
start the pinned container is `STOP_INFRASTRUCTURE`. No retries or replacement
formal output.

## C — competing explanations

The hand-authored corpus and oracle may share omissions or favorable
assumptions. Exact agreement can be a fixture-construction result rather than
evidence of real Agent Action coverage. The shape may simply repeat prior
contracts instead of representing a necessary new abstraction.

## U — limits

No learned router, runtime integration, GUI/task input, verifier truth,
independent-human audit, latency/efficiency, safety improvement, ontology
completeness, or cross-domain claim. The `deadline` slot is represented but no
clock value is measured. The `UNKNOWN_CHECK_REQUIRED` flag is a conservative
fixture marker, not a novelty detector. This finite study informs #5268 only;
#5269 and #5275 remain gated on a frozen IR and are not tested here.

## Existing-evidence boundary

PR #5283 merged #5274's finite typed reducer, not a Verification IR. Its
retained rules distinguish `CURRENT` target evidence from `VERIFIED_EFFECT`
results and explicitly avoid authority promotion. Closed #4157 separately
established a scoped deadline-validity contract. Live #17 covers the safety
plane. The current #701 issue is an applicability-envelope review; this plan
does not attribute a typed evidence schema to it even though #5268/#5269 cite
that number as an evidence-role dependency. This cross-reference mismatch is
retained as a coordination note, not silently repaired by this experiment.
