# #1721 minimal partial-DAG recomputation under evidence-version changes

Decision: **PASS_PARTIAL_DAG_RECOMPUTATION_BOUND_SCOPED**.

## Result

The retained all-or-nothing reuse lattice from #1702 can be safely refined for pure compute DAGs when every node declares complete dependencies and evidence versions have #1675 exact semantic identity semantics.

A cached compute node is universally reusable iff no changed evidence leaf lies in its transitive dependency closure. Therefore the **minimal universally safe recomputation set is exactly the forward-reachable compute descendants of changed evidence**.

Formal exhaustive domain:
- 3 evidence leaves;
- 4 topologically ordered compute nodes;
- every compute node has every possible nonempty parent subset from evidence plus earlier compute nodes;
- **205,065 labelled DAGs**;
- every one of 7 nonempty evidence-change sets;
- **1,435,455 DAG/change-set states**.

Candidate transitive-closure invalidation matched an independently structured forward edge-propagation oracle in every state: mismatch **0**.

Across the exhaustive domain:
- dirty compute nodes: **4,874,310**;
- necessity witnesses established: **4,874,310 / 4,874,310**;
- cases where minimal partial recomputation is a strict subset of whole-job rebuild: **519,750**;
- direct-evidence-only invalidation missed **836,241** transitive stale descendants;
- blindly reusing all cached partials would reuse **4,874,310** dirty nodes.

Dirty-node count distribution across all 1,435,455 states:
- 0 dirty: 30,240
- 1 dirty: 62,370
- 2 dirty: 132,300
- 3 dirty: 294,840
- 4 dirty: 915,705

## Theorem boundary

`PROOF.md` gives the necessity/sufficiency argument. If a changed evidence leaf lies in a node's transitive closure, a deterministic parent-projection construction along one ancestry path provides a concrete function family where that node's output changes. Thus omitting any dirty node from the recomputation frontier cannot be universally safe.

The theorem requires complete declared dependencies, deterministic pure nodes and exact non-reused semantic version identities. The hidden-dependency control is explicitly rejected; side effects, nondeterminism and approximate evidence equivalence remain outside scope.

## Verification

- formal invocation1 / reruns0 / replacements0 / tuning0
- parent #1702 RESULT Git blob `529c3939b5ff4ac58ce71b7dad9d06e1409d64c8`
- parent #1675 REPORT Git blob `acb545678ac80da917d80bb40fedd8f84624ae92`
- independent edge-propagation audit PASS
- copied-result corruption controls 6/6 rejected
- authority/task-success promotions0

## Interpretation

This result does **not** prove a runtime speedup. It establishes the correctness boundary needed to avoid discarding all planner-gap background work after a local evidence change. Independent cached branches may survive; only the changed evidence's descendant frontier must be recomputed.

A useful empirical successor should instrument one real observation/verification pipeline as a declared compute DAG and measure how often evidence changes invalidate a strict subset rather than the whole pipeline, while checking that no hidden dependency invalidates the theorem assumptions.
