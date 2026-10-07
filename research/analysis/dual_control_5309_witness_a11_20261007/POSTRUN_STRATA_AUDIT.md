# A11 post-run stratum reclassification (v2)

This is a read-only diagnostic over A11's immutable candidate input, selected actions, raw environment outcomes, and oracle. It does **not** rerun candidate/environment/auditor, change the frozen formal verdict, or replace the original `audit.json`.

## Reason for this diagnostic

The frozen auditor grouped cases as “correct over budget” whenever `action-b` cost exceeded budget, regardless of which action actually preserved the witness. But `action-a` always costs zero. In rows where `action-a` is the actual preserving action and `action-b` is expensive, preservation is still affordable. This makes the original correct-affordable / over-budget labels inaccurate, even though the frozen row reconstruction itself is preserved.

## Corrected rule

Using actual topology-derived transitions from the retained oracle, first identify the set of witness-preserving actions. For correct predictions with no preexisting witness:

1. `correct_affordable`: at least one actually preserving action costs no more than budget;
2. `correct_over_budget`: at least one actually preserving action exists, but every such action exceeds budget;
3. `correct_no_preserving_action`: no action in the admissible set preserves the witness;
4. `misspecified`: predictions differ from the actual transition-derived map;
5. `prior`: a witness exists before the action and is reported separately.

The standalone read-only program `audit_retained_strata_v2.py` reconstructs actual witness receipts and decisions for all retained 264 arm rows and reports source hashes. It is a post-outcome audit, not a preregistered/formal A11 gate.

## Disposition

See `POSTRUN_STRATA_FREEZE.md` for diagnostic input/source hashes and `audit_retained_strata_v2.json` for the one-shot result. Regardless of this diagnostic's result, A11 remains formally `FAIL_AUDIT_MISSPECIFIED_STRATUM_GATE`; the A11 formal raw files and first audit are unchanged.
