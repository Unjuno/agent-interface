# Preservation qualification — Issue #5805 exploratory T0

This additive note records a read-only review of the evidence originally retained at PR #5818 head `a8ddcdf518d62781618010b4159f9834b0ba21c2`. The thirteen original evidence files remain byte-for-byte unchanged; `RETAINED_BLOB_INVENTORY.json` records their Git blob identities, byte lengths and SHA-256 values. All eleven hashes declared by the frozen package and report match. Candidate, auditor and construction tests were not rerun for this preservation review.

## Scientific scope remains unchanged

The retained `PASS_METHOD_SCOPED` is an exploratory, fixture-authored finite authorization-admission result: 17 traces by four policies, 68 rows. It is not a formal Issue allocation. All retained rows have `effect_applied=false` and `effect_verified=false`; the audit reports zero effect receipts. No real owner discovery, human consent, shared-resource effect, concurrent ownership, GUI behavior, legal conclusion or product-safety result is established.

The [owner's post-run review](https://github.com/Unjuno/agent-interface/issues/5805#issuecomment-5925564407) identifies an uncovered combined-evidence cell: a current authentic direct DENY together with an otherwise matching delegation. In the frozen source, the direct-grant check returns false for DENY, after which the scoped-delegation branch can still accept a matching delegation. The frozen fixtures test veto and delegation separately. The retained enumerated PASS therefore does not establish direct-veto dominance under combined evidence. This source-review limitation is preserved rather than repaired or relabeled; no new counterexample was executed.

Merged #5816 and this exploratory record have distinct coverage and must not be pooled. Issue #5805 remains a research question. Any later validation would need its own explicitly declared precedence contract and authorization; preservation does not create an experiment allocation.

## Repository maintenance boundary

Navigation and ordinary repository-maintenance checks concern archival integration only. They do not rerun or upgrade the frozen experiment. The original source, fixture, manifests, raw decisions, audit and narrative remain intact; this qualification and the inventory are separate append-only records.
