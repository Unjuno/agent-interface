# Issue #5547 T0 — finite invariant-confluence boundary

Status: preregistration, written before the sole formal container invocation.

## H/T/D/C/U

- **H:** Under the exact finite state/join contract below, the declared `monotone_safe` deltas preserve the safety invariant for every unordered pair, while `coordination_required` operations have at least one unsafe pair that a classifier detects. Unknown operation/schema forms fail closed.
- **T:** Exhaustively enumerate the Cartesian product of two deltas for each operation over the finite value domains; compare the candidate's classification with an independently implemented direct state oracle. Validate every pair in both application orders, join idempotence/commutativity, and corruption controls. One run in a digest-pinned, network-disabled Docker container.
- **D:** PASS only if all candidate-labelled monotone pairs satisfy the invariant, every operation labelled coordination-required has a counterexample pair, all oracle comparisons agree, join algebra controls pass, and all corruption controls are detected. Any unsafe monotone pair or missed coordination counterexample is FAIL. Model/schema incompleteness is retained as a scope limit, never inferred PASS.
- **C:** A richer invariant, missing field (especially freshness/authority), concurrent revoke semantics, or non-idempotent external effect can make the selected join inappropriate. The test may be validating hand-selected labels rather than discovering a generally useful classification.
- **U:** Pure finite synthetic semantics only. No production state schema, distributed store, transport, concurrency schedule, external effect, latency, availability, or real coordination-cost measurement.

## Frozen contract

State is `(evidence: set[str], admitted_claims: set[str], revoked_claims: set[str], authority_epoch: int, quota_reservations: set[str], effect_committed: bool)`. Join unions the four sets, takes the maximum authority epoch, and ORs the effect bit. The finite domains are evidence `{e0,e1}`, claims `{c0,c1}`, epoch `{0,1}`, reservation identities `{r-left,r-right}`, and effect `{false,true}`. All generated pairs start at the empty bottom state and apply one delta per replica.

Invariant: the number of quota reservations is at most one; an effect may be committed only at authority epoch 1 and only if evidence `e0` is present; a revoked claim may never coexist with that claim in the admitted set. (There is one boolean effect bit, so duplicate effect receipts are idempotent in this deliberately narrow model; real external effects are explicitly out of scope.)

Operations under test:

| Operation | Candidate label | Merge semantics |
|---|---|---|
| `ADD_EVIDENCE` | monotone_safe | add one evidence token |
| `REVOKE_CLAIM` | monotone_safe | add one revoked-claim token |
| `RECORD_IDEMPOTENT_RECEIPT` | monotone_safe | add one unique receipt token to evidence |
| `REFRESH_EPOCH` | coordination_required | set epoch to 1 |
| `RESERVE_QUOTA` | coordination_required | each replica contributes a distinct reservation identity (`r-left` or `r-right`); merge unions reservation identities |
| `COMMIT_EFFECT` | coordination_required | set committed bit |
| unknown operation | coordination_required | refuse classification |

The test will enumerate same-operation and cross-operation pairs, including only pairs whose deltas are individually valid from the common base. “Coordination required” is operationalized narrowly as existence of an invariant-violating joined pair involving that operation. This does not claim the converse for arbitrary programs or prove that every such pair needs a particular locking protocol.

## Formal result review / successor rationale

Formal allocation `issue-5547-iconfluence-t0-20261001-01` emitted 81 pair rows and initially passed the first independent invariant checks. The stricter independent idempotence review returned **FAIL**: quota reservation was represented as an unlabelled integer and joined by addition, so even joining one reservation delta with itself doubles it. Replacing addition with max would instead erase a concurrent independent reservation. The candidate model therefore failed to encode operation identity. Preserve its raw output and failure unchanged under `results/formal-01/`; do not rerun or relabel it.

Successor `issue-5547-iconfluence-t0-20261001-02` changes only the frozen representation of quota reservation to a set of unique replica reservation IDs and uses set union. Its purpose is to test whether the failure was a representation defect and whether a two-replica over-quota witness remains while same-delta replay is idempotent. It is a new identity, source hash set, and output directory.

## Preflight record

An isolated Docker construction preflight (not the formal allocation) exposed that a first quota sketch used `max(local reservation)` and consequently had no two-reservation counterexample. The formal allocation above then used an unlabelled integer with additive join, which the stricter idempotence auditor correctly rejected. Successor 02 models reservation identities directly. Both preflight output trees and formal-01 raw output/failure remain preserved and will not be relabelled as successor results.

## Independence and artifacts

The candidate classifier and join implementation live in `candidate.py`. `auditor.py` imports neither; it rebuilds states from primitive frozen input rows and checks the invariant directly. Raw candidate rows are immutable input to the auditor. `corruption_controls.py` mutates one classification, one join field, and one output row; each must be rejected. The formal run records exact command, image digest, source hashes and stdout/stderr/exit status.

Allocation identities: formal-01 `issue-5547-iconfluence-t0-20261001-01` (consumed; retained audit FAIL) and successor formal-02 `issue-5547-iconfluence-t0-20261001-02` (one invocation only). A runner/infrastructure failure for either identity is STOP and will not be retried.

Successor-02 preflight used the candidate JSON from `results/successor-02-preflight/` and did not execute the candidate again. The independent auditor and all five corruption controls pass after audit-harness corrections. Formal-02 source hashes are frozen separately in `FREEZE-02.json`; its formal output destination is `results/formal-02/`.
