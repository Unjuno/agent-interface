# Issue #5547 successor T1 — history-dependent join closure

Source main `2b2166da7e1e3b4e60e435b6c7857484797a23ec` is frozen in `FREEZE.json`. This is a distinct successor allocation from #5558's pre-test invocation STOP; the prior files and failure remain unchanged.

## H / T / D / C / U

- **H:** A root-state-only join probe cannot certify history-dependent `COMMIT` operations as safe when their enabling precondition is absent initially; a reachable-state closure will find that two individually valid commits for the same semantic effect can merge into an at-most-once violation, while the serializable baseline refuses the second commit.
- **T:** Enumerate the frozen command alphabet from the empty state to depth two. For each reachable base state, apply every pair of enabled commands independently, check the join, compare both serial orders, and retain the shortest counterexample. Run the one discovery-based unittest command, one runner, then one raw-only independent audit with five frozen in-memory corruptions.
- **D:** PASS only if root-only marks COMMIT `NOT_PROVEN` (never safe), reachability finds the expected duplicate-effect witness after authorization, both branch states are invariant-valid, their join violates exactly the at-most-once invariant, serial execution remains valid, and the audit rejects all five corruptions. Missed witness or unsafe root certificate is FAIL. Dependence on changed preconditions is UNCERTAIN.
- **C:** A protocol that binds authorization and commit into one indivisible, globally unique token may make the join-safe prefix larger; that design is not modeled here.
- **U:** This finite history-dependent boundary does not prove a general checker sound or complete, nor establish backend idempotence, distributed delivery, performance, or production safety.

## Fixed state and safety contract

State is `(authorized_effects, commit_records)`. `AUTHORIZE(effect)` adds a persistent authorization. `COMMIT(dispatch,effect)` is enabled only when authorized and no commit for that semantic effect exists locally. The invariant is at most one commit record per semantic effect, and every commit must be authorized. Join is fieldwise set union. Unknown commands fail closed.

The independent auditor is a separate implementation and does not import the candidate model or runner.
