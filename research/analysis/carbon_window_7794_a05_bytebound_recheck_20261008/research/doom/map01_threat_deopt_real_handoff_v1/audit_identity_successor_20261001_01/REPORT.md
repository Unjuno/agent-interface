# Issue #626 audit identity successor — result and provenance STOP

## Outcome

**Overall: `STOP_LEGACY_SOURCE_HASH_MISMATCH`.** The synthetic candidate generator and new raw-only auditor each ran once. The new auditor reported `PASS_AUDITOR_IDENTITY_BINDING_SCOPED` for six synthetic rows, zero errors. Pre-freeze construction tests were 4/4. However, the local file labelled `legacy_audit.py` does **not** match the exact frozen legacy auditor source SHA-256 in Issue #626. Therefore the old-auditor mutation comparison is not authenticated against the original, the frozen decision rule is not met, and this bundle is not a verified successor to the #626 frozen audit. Do not interpret the legacy synthetic PASS or mutation controls as a reproduction of the frozen source.

The observed local legacy-file SHA-256 is `14a5f6a8c7a5ba208aa15d24b983735486e29f8519a817cf640399b5314e950d`; the frozen original source SHA-256 is `7ab3d8895c9e8d7c80cf4ff463bac0623fb39247f8aa0d65f34941a1f8c48a40`. The frozen archive SHA-256 remains recorded as `e95dd3fd3992c70be54a4e16530fb26d71ab94d88054f2900f656aee53d8462a`. No repair, retry, or source substitution was made after the one-shot run.

## H / T / D / C / U

**H.** An independent auditor can enforce the six-case identity tuple and retain the semantic checks summarized by the frozen #626 auditor.

**T.** Host-only synthetic construction: six deterministic rows from the frozen case/fixture identities; four in-memory unit tests; then exactly one candidate generator and one new auditor invocation. No Docker/OrbStack, ViZDoom, X11, model/provider, GUI, or input.

**D.** Intended pass required matching the exact archived old-auditor source hash, clean semantic and identity audit, and all mutation controls. The source hash mismatch makes the overall result STOP regardless of the new auditor's local synthetic pass.

**C.** The raw rows are synthetic and only exercise a finite contract. They are not MAP01 sessions or physical effects.

**U.** This does not authenticate the original #626 evidence, repair its audit, establish the handoff-fence hypothesis, authorize formal sessions, or change the original 0/6 allocation. The original bundle and schedule remain untouched. The new auditor should not be used for the formal run pending exact-source comparison and independent review.

## Preserved observations

- Construction: `python3 -B -m unittest -v test_contract.py` — 4 passed before freeze.
- Candidate: `python3 -B candidate.py` — one invocation; six rows; exit 0.
- New auditor: `python3 -B audit.py` — one invocation; `PASS_AUDITOR_IDENTITY_BINDING_SCOPED`, zero errors; exit 0.
- Pre-freeze in-memory controls rejected ID, runtime SHA, fixture ID, seed, arm and completeness mutations in the new auditor. The local legacy transcription accepted four identity mutations, but because its source hash is wrong this is **not** evidence about the exact frozen auditor.
- After run, six frozen input source hashes rechecked successfully. Python compilation and the four construction tests passed again; neither command reran the candidate or raw auditor.
- GitHub main was `45a1e0de5d8ccb45959b6e59a71fc5e8ec93cc3f` at publication check, newer than the preregistration base `7e94ba9fdbfbff8d32d5dde27c086f2eb7582775`. The target additive directory was absent on main and the queried branch search found no matching branch. This source advancement does not repair the legacy source mismatch.

Raw output and every intermediate are preserved unchanged. `POST_RUN_AMENDMENT.md` corrects the misleading frozen-source description without altering it. See `FREEZE.json`, `candidate_raw.json`, `audit_result.json`, `legacy_audit_result.json`, `mutation_results.json`, and `SHA256SUMS`.
