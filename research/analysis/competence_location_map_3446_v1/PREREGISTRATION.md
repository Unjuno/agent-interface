# Competence-location map: preregistration

Allocation `competence-location-map-3446-20261001-01`; frozen against main
`07c5a1bbff1ba82e0ffdcd0f521fe2102a59ad51`. This tests the unverified
competence-location refinement attached to Issue #3446, not the earlier
48-row static router experiment. No production or runtime router is changed.

## H / T / D / C / U

**H.** A map that retrieves specialist competence from independently scored,
version-current, unexpired evidence will improve exact specialist location and
reduce needless YIELD over static overlapping scope declarations and a
success-record-only selector, while preserving required YIELD and zero
authority.

**T.** Compare `STATIC_SCOPE`, `RECENT_SUCCESS_ONLY`, and
`VALIDATED_COMPETENCE_MAP` on 56 deterministic held-out episode records: seven
predeclared strata × eight records (browser/file/GUI overlap, adapter-version
replacement, expired success evidence, unavailable specialist, and novel mode).
Each policy emits proposals only; a shared final gate checks declared scope,
current availability, version, and evidence provenance/expiry. Retain all 168
policy rows and their input cases. The map additionally requires independent
oracle provenance, current adapter version, unexpired evidence, support `n>=2`,
declared task-family scope, and present availability. Support episode IDs are
disjoint from held-out episode IDs. No model, training, task action, or input
authority is involved.

**D.** `PASS_COMPETENCE_LOCATION_MAP_CONSTRUCTION_SCOPED` only if the candidate
and separate raw-only auditor exit 0; all 56 cases/168 policy rows and all seven
8-row strata are present; the map routes exactly at least 39/48 known cases and
exceeds each control by at least 10 exact routes; it yields on all 8 novel-mode
cases; all policies have zero novel admissions, authority grants, and input
emissions; and all four auditor mutation controls are rejected. A valid policy
mismatch is FAIL; missing/hash/audit/transport evidence is STOP. One candidate
invocation only, no retry or post-result tuning.

**C.** All policies receive the same authored task family, current version,
availability, declared scopes, and evidence ledger. The synthetic oracle is
specified independently in the audit source. `STATIC_SCOPE` uses fixed adapter
priority; `RECENT_SUCCESS_ONLY` chooses the highest recorded score without
checking its provenance, version, expiry, or availability before proposal; the
map filters those conditions before selection. The shared final gate prevents
invalid proposals from gaining even advisory route admission. Work units count
scope/evidence inspections; they are deterministic lookup-cost proxies, not
latency measurements.

**U.** This is an authored finite construction discriminator on one Windows host
and one local Docker Linux/amd64 engine. The repeated cases do not estimate a
population distribution. Evidence and oracle are synthetic; no actual browser,
file, GUI adapter, independently scored application effect, learned router,
cross-app generalization, end-to-end benefit, production safety, or human-team
memory transfer is established. The map intentionally performs more lookup
work, whose real wall-time/benefit tradeoff remains unmeasured.

## Frozen gates and execution

The exact hashes, image digest, resource limits, and commands are in
`FREEZE.json`. Candidate and auditor source SHA-256 values are frozen there.
Construction tests run first in Docker using that same pinned image. The
candidate and independent auditor then run in separate networkless containers;
source and candidate raw are mounted read-only to the auditor. Only output
directories are writable. Preserve first outcome without retry.
