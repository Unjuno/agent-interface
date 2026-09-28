# #5126 audit-integrity successor v4

## H — hypothesis

A raw-only auditor that validates both the pinned input corpus identity and the
selected effect identity reconstructed from raw records will reject (a)
self-consistent case substitution under a stale digest and (b) candidate plus
oracle outputs corrupted to the same arbitrary effect ID, while accepting the
unmodified, corrected v3 contract result.

## T — finite experiment

Use only the immutable #5126 v1 raw corpus (SHA pinned below) and the separately
frozen v3 candidate/oracle logic. Generate one 13-row v4 result, then run one
raw-only audit. Before freeze, run construction tests that mutate case content
and both serialized classifier effect IDs after classification; both must be
rejected for the intended identity-integrity reason. No model, GUI, input,
network, GPU, or container; the #5126 container slot is not assigned.

## D — gates

PASS requires: the auditor verifies the corpus SHA-256 and exact ordered
`(case_id, raw)` rows against the pinned source; candidate and oracle outputs
match; the auditor independently derives physical/task-effect outcomes and
requires each selected `effect_id` to equal the sole qualified raw event ID;
the two corruption controls are rejected; all 13 expected labels match; all
authority flags remain false; and prior v1/v2/v3 artifacts remain unchanged.

## C / U

This strengthens synthetic evidence integrity only. The merged #5141 schema
audit still holds current producer source identity/epoch availability. No live
lineage, task efficacy, efficiency, or runtime readiness follows.
