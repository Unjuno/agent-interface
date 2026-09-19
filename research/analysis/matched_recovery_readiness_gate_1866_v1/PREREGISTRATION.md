# Issue #1866 — matched recovery efficacy entry gate v1

Status: FROZEN CONSTRUCTION / NO LIVE ALLOCATION

## H/T/D/C/U

- H: A five-plane evidence gate prevents a future matched MAP01 recovery allocation from being authorized when any required plane is missing, active, weakly typed, or unbound.
- T: Enumerate all 2^5 readiness vectors and classify only the all-ready vector as AUTHORIZE. Apply adversarial relabeling controls for viewport/HUD/terminal evidence, open prerequisites, and pair summaries without arm binding.
- D: Standard-library candidate, independent oracle, 32 gate vectors, five corruption controls, exact counts, digest, and zero input/model/GUI actions.
- C: Evidence laundering, active prerequisite treated as ready, missing arm binding, weak evidence promoted to TASK_EFFECT, or candidate/oracle disagreement.
- U: This does not establish that a live allocation is useful, safe, or ready in the real environment. It only tests the admission classifier.

## Gates

1. physical actuation with lineage and occupancy evidence;
2. independent plan-bound TASK_EFFECT or explicit unresolved/no-effect;
3. matched recovery/coast arm definition;
4. arm-level audit binding;
5. independent release/terminal/integrity evidence.

## Disposition

PASS_MATCHED_RECOVERY_ENTRY_GATE_HOLD_SCOPED is expected for the current snapshot if any gate is incomplete. AUTHORIZE is a classifier output only; it is not a lease or permission to run MAP01.

## Stop rules

One construction invocation, no reruns/replacements/tuning. Any source/readback mismatch, oracle disagreement, or weak-role promotion is FAIL_INTEGRITY / FAIL_EVIDENCE_LAUNDERING. No live allocation is launched by this fixture.
