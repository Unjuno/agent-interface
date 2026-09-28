# Strict task-effect lineage successor — Issue #5126

## H — hypothesis

The contract can fail closed on whitespace/non-string lineage and on missing
or duplicated immutable source-event references, while retaining a single
well-formed synthetic positive and keeping state feedback non-authoritative.

## T — finite experiment

Use a deterministic standard-library-only corpus with a canonical valid
positive and hostile mutations for each lineage ID, physical DOWN/UP source
event ID, scorer source-event ID, duplicate IDs, and malformed types. Run an
independent oracle, tests, then a raw-only auditor that imports neither.
Preserve raw bytes and SHA-256 hashes. No GUI, model, input, network, GPU, or
container. This is host CPU contract work and is not a Docker allocation.

## D — gates

PASS requires candidate/oracle/expected agreement on all frozen cases; each
identifier is an exact nonempty canonical string (`value == value.strip()`);
DOWN and UP source event IDs differ; the effect source event ID is nonempty;
duplicate source event references or effect identities fail closed; raw-only
audit reconstructs these conditions from raw records; authority remains
false. If the actual retained source schemas cannot attest unique IDs, report
HOLD rather than synthesizing an identity and implying production readiness.

## C / U — boundary

All evidence is synthetic. This validates only the finite serialization and
lineage contract. It does not establish live source-schema availability,
causality, physical input, task efficacy, model usage, efficiency, or product
readiness. The v1 result and its correction are separate immutable evidence.
