# #5126 strict lineage v3 — freeze after construction gate-taxonomy repair

## H — hypothesis

Keep two distinct refusal reasons: (1) a scorer source ID colliding with a
physical DOWN/UP source ID is `UNRESOLVED_DUPLICATE_SOURCE_EVENT`; (2) repeated
scorer/effect rows remain `UNRESOLVED_DUPLICATE_EFFECT`. A typed, disjoint
identity namespace would be an alternative, but the synthetic schema has no
producer-grounded namespace tag, so it is not assumed.

## T — finite experiment

Read only the hash-pinned #5126 v1 corpus; rerun the corrected v3 candidate,
separate oracle, and raw-only auditor over its 13 fixed cases. Do not alter v1
or v2 artifacts. Construction tests run before freeze; then pin all v3 code,
plan, test, input corpus digest and expected decision before one formal corpus
run and one raw-only audit. No container, GUI, model, input, network, or GPU;
the #5126 CPU container lane is not assigned.

## D — gates

PASS requires 13/13 candidate-oracle and expected-label agreement; physical
DOWN, UP, and scorer IDs are pairwise distinct for TASK_EFFECT_SCOPED;
cross-plane collisions and duplicate scorer/effect rows fail closed under the
separate statuses above; raw-only audit reconstructs both distinctions and
detects a post-classification raw collision; all authority flags are false;
all prior v1/v2 artifacts retain their recorded hashes.

## C / U

This only repairs the synthetic contract taxonomy and collision rejection.
The merged #5141 source-schema audit says current producers lack source IDs
and a shared epoch key. No live source availability, causality, task efficacy,
efficiency, or product-readiness claim follows.
