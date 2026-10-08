# #5126 strict lineage contract v2 — cross-plane identity collision

## H — hypothesis

An untyped `source_event_id` namespace shared by physical DOWN/UP edges and
independent scorer events is ambiguous: a scorer event reusing a physical
edge ID must not qualify as a plan-bound task effect. Candidate, separate
oracle, and raw-only audit can all fail closed on that collision while
retaining the other canonical positives.

## T — frozen successor corpus

Use the retained #5126 v1 synthetic raw corpus (SHA-256 pinned in
`FREEZE.json`) as immutable input. Re-evaluate all 13 cases with separate v2
candidate/oracle/raw-auditor implementations. Change only the expected
classification of `cross_plane_event_id_collision` to
`UNRESOLVED_DUPLICATE_SOURCE_EVENT`. Add a unit sensitivity test that mutates a
previously valid retained positive after classification and requires the
raw-only auditor to reject the stale result. Host standard-library CPU only;
no container, GUI, model, input, network, or GPU.

## D — gates

PASS requires all 13 rows to match between candidate, oracle, and v2 expected
gate; physical DOWN, physical UP, and scorer source-event IDs are canonical
and pairwise distinct for a scoped task effect; the raw-only auditor
reconstructs that rule without importing candidate/oracle; the mutated raw
collision is caught; authority remains false; prior #5126 v1 inputs/results
remain byte-identical.

## C / U

This resolves only the synthetic untyped-namespace contract defect. Current
main producer schemas still lack a cross-plane epoch/source identity (see the
merged #5141 audit); no live task-effect, causal, runtime, efficiency, or
product claim follows. This is not a container result; #5126 has no Docker
slot assignment.
