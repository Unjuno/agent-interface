# Git tree revalidation + current-OID CAS

Decision: **RETAIN scoped semantic-tree revalidation plus current-OID CAS**. Issue #290.

## Question
The prior rung showed that exact plan-time OID CAS prevents stale writes. This rung asks whether that guard is over-strict when the ref now points to a different commit with the exact same tree/content.

## Frozen design
Real local Git 2.47.3, sixty fresh repositories: exact-old CAS versus tree-revalidate/current-OID CAS across stable, semantic-same replacement, and semantic-different replacement; ten first outcomes per cell. Semantic-same C is a distinct commit object with `C != A` and `C^{tree} == A^{tree}`. Semantic-different D has a different tree.

Candidate algorithm: read current OID X, check `X^{tree}` against the plan-time A tree, and only if it matches issue `git update-ref target B X`. The final old-OID argument binds publication to the exact current state whose tree was checked. A prefreeze unit test changes the ref again after the tree check and confirms this final CAS rejects the race.

Freeze commit: `dae9660145d49528b434130677cdf6385900a2ab`.

## Results
- exact-old / stable: 10/10 correct.
- exact-old / semantic-different: 10/10 correct reject.
- exact-old / semantic-same: **0/10 correct; false reject 10/10**.
- tree-current-CAS / stable: 10/10 correct.
- tree-current-CAS / semantic-same: **10/10 correct accept**.
- tree-current-CAS / semantic-different: **10/10 correct reject**.

All 60 cases pass the independent integrity audit. No measured ID was rerun.

## Interpretation
This is a concrete version of `predicate revalidation + identity-bound commit`: use a semantic predicate to decide whether the delayed operation is still valid, then bind the consequential update to the exact current identity that was evaluated. It avoids exact-version false rejects in this authored Git task without reopening a TOCTOU write race on the ref.

Tree equality is **not general semantic equivalence**. Commit metadata, ancestry, signatures or other state may matter to another task even when the tree matches. The semantic predicate must therefore be task-defined or effect-owner-provided; this experiment does not discover it automatically.

## Verification
Four prefreeze tests pass, including a deliberate post-check ref change that is rejected by the current-OID CAS. A separate extraction reruns all four tests and the independent 60-case audit. The retained manifest covers 2,233 files with zero SHA-256 mismatches.

Full raw evidence is conversation/container-only: `git_tree_guard_evidence.tar.xz`, 84,724 bytes, SHA-256 `56c289e514d633073f0e0bd1ef419122a61abe9f7da6c111ba5965bdeb6708bf`.

## H / T / D / C / U
**H:** semantic revalidation plus CAS-current removes exact-OID false rejects while preserving stale-write protection.

**T:** frozen 60-case matrix, four prefreeze tests including post-check-race rejection.

**D:** scoped PASS / retain; candidate 30/30 correct, exact-old false rejects 10/10 semantic-same.

**C:** candidate has an additional task-specific tree predicate.

**U:** one Git build/host/ref; no arbitrary GUI semantics, automatic predicate discovery, multi-ref transaction, network or power-loss claim.
