# Git dependency-scoped revalidation + current-OID CAS

Decision: **RETAIN scoped dependency-path revalidation plus current-OID CAS**.

## Question
The prior rung showed that whole-tree equality can safely gate a delayed Git ref update, but it may reject changes outside the delayed operation's actual dependency set. This rung narrows the semantic predicate from the whole tree to one declared dependency path, `dependency.txt`.

## Frozen design
Real local Git 2.47.3, sixty fresh repositories: `tree_current_cas` versus `path_current_cas` across stable, unrelated-file change, and dependency-file change; ten first outcomes per cell. Freeze commit `860f62ff4b0109faf3d5304d43d230d5dd0324b2` precedes measurement.

Both candidates read current target OID X and finish with Git-native `update-ref target B X`. Only the predicate differs. Whole-tree compares `X^{tree}` with plan-time `A^{tree}`. Path-scoped compares the current `dependency.txt` blob OID with the plan-time dependency blob. The final current-OID CAS binds the write to the exact identity whose predicate was checked.

## Results
- whole-tree / stable: 10/10 correct accept.
- whole-tree / dependency changed: 10/10 correct reject.
- whole-tree / unrelated changed: **0/10 correct; false reject 10/10**.
- path-scoped / stable: 10/10 correct accept.
- path-scoped / unrelated changed: **10/10 correct accept**.
- path-scoped / dependency changed: **10/10 correct reject**.

Path-scoped candidate: **30/30 ground-truth correct**. All60 cases pass the independent integrity audit. No measured ID was rerun.

## Race control
A prefreeze unit test validates `dependency.txt`, then changes the target ref before commit. The final `update-ref target B X` rejects because X is no longer current. Thus narrowing the semantic predicate does not remove the identity-bound commit check.

## Interpretation
This is a concrete dependency-scoped form of `predicate revalidation + identity-bound commit`. A declared dependency footprint can prevent unrelated changes from invalidating a delayed action while still refusing a change to the dependency itself.

The dependency is **authored and complete by construction**. The experiment does not discover hidden dependencies, prove arbitrary GUI dependency completeness, or show that one path/blob is sufficient for other tasks. A missing dependency would make this mechanism unsound rather than merely less available.

## H/T/D/C/U
H: narrowing revalidation to a declared dependency removes whole-tree false rejects without reopening stale writes. T: frozen60-case Git matrix plus prefreeze TOCTOU race test. D: scoped PASS/retain; path candidate30/30 correct, whole-tree false reject10/10 unrelated changes. C: gain comes from extra task-specific dependency knowledge. U: one Git build/host/ref/path; no automatic dependency discovery, GUI/model/network/power-loss or multi-ref transaction claim.
