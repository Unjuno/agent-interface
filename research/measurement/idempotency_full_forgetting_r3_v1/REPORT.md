# #24 full-forgetting ambiguity R3

Decision: **PASS_FULL_FORGETTING_AMBIGUITY_SCOPED**

## Question
R1 established status-before-retry. R2 established that a known expired may-have-effect identity cannot safely be collapsed into ordinary replay-eligible `NOT_FOUND`. R3 asks whether the last retained identity marker can itself be forgotten without adding another source of information.

Two hidden histories are constructed to be observationally identical after complete forgetting:
- `NEVER_SEEN`: no input/effect ever occurred; direct retry is the live action.
- `COMPLETED_FORGOTTEN`: one non-idempotent effect occurred, then all retained identity/status/effect evidence expired; direct retry duplicates it.

Both expose exactly the same status-only observation: matching requested scope, same parameter-shape label, `NOT_FOUND`, no retained provenance and no effect evidence.

## Exact model check
Six context decorations are paired with both hidden histories. Every deterministic status-only policy in `{RETRY, NO_REPLAY, REQUIRE_EXTERNAL_EVIDENCE}` is exhaustively evaluated: 6 pairs ×3 policies =18 evaluations. One invocation; reruns/replacements/tuning 0.

- observable mismatch within hidden-history pairs: **0**
- direct policies satisfying both safety and immediate retry liveness: **0**
- `RETRY` duplicate-effect pairs: **6/6**
- `NO_REPLAY` blocked-never-seen pairs: **6/6**
- `REQUIRE_EXTERNAL_EVIDENCE` duplicate-effect pairs: **0/6**, but the result remains unresolved rather than immediate retry success
- false COMPLETED claims: **0**
- digest: `95e13c2ef66b851a64cca40996b0c982d366a7f2dfa801f66f98b35d7052adf6`

Independent audit reproduces the enumeration exactly and four copied-result mutations are rejected.

## Interpretation
With complete forgetting and no independent application-effect evidence, the two histories are indistinguishable to a status-only recovery policy. `RETRY` chooses liveness and loses duplicate-effect safety; `NO_REPLAY` chooses safety and loses never-seen retry liveness. A conservative external-evidence requirement is safe but explicitly unresolved.

Therefore an implementation that wants both properties must preserve or recover some discriminating information: for example content-bound identity/outcome state, independent effect observation, application-owned idempotency/deduplication, a non-reusable identifier regime, or another operation-specific policy. The model check does not select one.

## Limits
This is a finite semantic information-boundary model, not a storage-byte lower bound, cryptographic uniqueness proof, durability experiment, GUI test or performance result. Random repetition would add no information, so none is used.
