# Issue #5442 T8 — actual intent-target binding control

Allocation: `SEMANTIC-RECEIPT-5442-T8-ORBSTACK-20261002-01`

## Why this successor exists

T7 and its open PR #6534 are preserved as HOLD. T7's control named `intent_target` changed only `scenario_id`; it did not mutate the actual target field. T8 is a distinct frozen successor that directly tests the target binding in the serialized receipt and in the scenario source. No T7 input, output, branch, or conclusion is edited or rerun.

## H / T / D / C / U

**H.** In a deterministic layered simulator, a successful dispatch to the wrong object can satisfy the requested goal on that other object while leaving the intended object unchanged. A receipt that binds intent target, dispatched target, authoritative observed target/state, and pre/post versions will remain `UNKNOWN` and deny an irreversible-commit admission; an intermediate-only policy will report success. The independent raw-only auditor will reject an actual mutation of `receipt.intent.target_id` (not a row/scenario label), plus source, endpoint-target, decision, and row-count corruptions.

**T.** Freeze this additive package against current main before formal execution. Run the candidate once and only once in a network-disabled, read-only-input OrbStack container from the pinned Python image. If and only if the candidate exits 0 and emits one parseable raw document, run the independent auditor exactly once in a separate network-disabled, read-only-input OrbStack container, with the candidate raw mounted read-only. No retries, source edits, pulls, installs, GPU use, or external service calls after freeze. Construction tests are separate and do not count as candidate/auditor invocations.

**D.** The frozen four-case table is: valid effect → intermediate `SUCCESS`, semantic `SEMANTICALLY_CONFIRMED`, commit admitted; wrong target (effect occurs only on the other object) → `SUCCESS`, `UNKNOWN`, no commit; stale pre-state → `SUCCESS`, `UNKNOWN`, no commit; no-op → `SUCCESS`, `UNKNOWN`, no commit. `PASS_TARGET_BINDING_SCOPED` requires exact raw-table reconstruction, source/allocation binding, successful rejection of the actual nested intent-target corruption and all other frozen controls, zero audit errors, and candidate/auditor exits 0. Any unmet gate is HOLD/FAIL with first outputs preserved. The result is limited to these authored deterministic fixtures.

**C.** The simulator's object store and its endpoint observer are fixture-authored and stipulated authoritative. This tests the protocol and audit wiring, not the fidelity of any real observer, UI, or application.

**U.** No claim about real-world semantic correctness, GUI/task effects, runtime authority, safety rates, latency/cost, or product benefit. Configured container limits will not be described as enforced unless independently observed.

## Frozen invocation accounting

Candidate maximum: 1. Auditor maximum: 1, and only after candidate exit 0. Retries: 0. Raw and audit output locations must be absent before the formal run. Preserve first outputs, commands, container inspect results, exits, stdout/stderr, hashes, and any infrastructure or audit failure.
