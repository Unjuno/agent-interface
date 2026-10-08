# #1882 source-first plan

TASK: `SAFETY-PLANE-DATA-CUTSET-R0-20260919-001`

BASE at intake: current main `24b9f73bdf7b8adeedb51527ed3f211e80ef52b3`.
Parent: #17. Related empirical safety-plane results: #810/#811/#814/#816/#821/#823/#827/#871. Collision search found no exact data-plane cut-set/release-reachability analysis or matching branch.

Additive scope only:
`research/analysis/safety_plane_data_cutset_r0_v1/**`

Standard-library deterministic container only. No GUI/X11/model/provider/network/task input/user data/shared runtime mutation. This is an analytical design discriminator, not a new safety implementation or empirical hard-real-time claim.

## Gap

#17 and its successors show several concrete failures/successes under blocked data paths, owner death and backend loss. The architecture rule is still stated operationally ("safety path must not depend on data plane") rather than as an exact dependency condition. In particular, "no single shared bottleneck" is not sufficient if two distinct data-plane vertices form a multi-vertex cut.

## Roadmap

1. Define a directed dependency graph with typed vertices `SAFETY`, `DATA`, `ACTUATOR`; triggers and release sink are explicit.
2. Prove the exact condition for release reachability under arbitrary failures drawn from the declared DATA set, plus the bounded-`k` version.
3. Exhaustively enumerate a finite DAG universe and compare the theorem criterion with a direct failure-subset oracle.
4. Include directed controls for coupled, fully independent, and two-route/second-order-cut architectures.
5. Freeze source before the one formal invocation; independently audit retained output and corruption controls.
6. Publish only the scoped analytical result. Any live/runtime transfer is a separate successor.

## H

Let `G=(V,E)` be a finite directed dependency graph, trigger `s`, required release injection `r`, and declared data-plane vertices `D ⊂ V \ {s,r}`.

1. **Arbitrary DATA-failure guarantee:** release remains reachable for every failure set `F ⊆ D` iff `G-D` contains an `s→r` path.
2. **Up-to-k DATA-failure guarantee:** release remains reachable for every `F ⊆ D, |F|≤k` iff every DATA-restricted `s→r` vertex cut has cardinality `>k` (with "no such DATA-only cut" treated as infinity).
3. Therefore checking only whether one DATA vertex dominates all `s→r` paths is insufficient: two disjoint DATA-routed paths tolerate any one DATA failure yet can both be cut by two DATA failures.

This concerns dependency reachability only. Backend acceptance/physical confirmation and hard timing remain outside the theorem.

## T

One exact finite formal:
- fixed topological vertices `s, d0, d1, a0, a1, r`;
- `D={d0,d1}`; enumerate every directed DAG using all forward edges under that order (15 possible edges = 32,768 graphs);
- for each graph, direct oracle enumerates all `F⊆D`;
- independently compute `G-D` reachability, minimum DATA-only cut size, and guarantees for `k∈{0,1,2}`;
- require theorem/oracle mismatch 0 across the full universe;
- directed controls:
  - coupled single DATA dependency: arbitrary-failure guarantee false, min DATA cut 1;
  - direct safety path outside DATA: arbitrary-failure guarantee true, no DATA-only cut;
  - two alternate routes, one through each DATA vertex: k=1 true, k=2 false, min DATA cut 2.
- independent auditor must recompute counts from retained rows without importing the formal implementation;
- corruption controls must reject altered reachability, altered minimum cut, and altered control classification.

One formal invocation; reruns/replacements/tuning 0.

## D

`PASS_SAFETY_PLANE_DATA_CUTSET_THEOREM_SCOPED` iff:
- all 32,768 DAGs are covered exactly once;
- arbitrary-failure criterion mismatch = 0;
- bounded-`k` criterion mismatch = 0 for k=0,1,2;
- all three directed controls match their preregistered classifications;
- independent audit passes;
- all corruption controls are detected;
- source freeze/integrity passes.

Any theorem/oracle mismatch => `FAIL_DATA_CUTSET_THEOREM`.
Any incomplete enumeration/integrity failure => STOP/scientific NONE.

## C

A graph model may omit scheduling, shared kernel/backend failure, hidden IPC dependencies or timing. A runtime can satisfy dependency reachability yet still release too late, or fail at the actuator/backend. Conversely, empirical success in one stall injection does not establish the graph condition for all declared failures.

## U

Primary uncertainty is model completeness: which real dependencies belong in V/E/D. The formal itself is exact over the declared finite graph universe; no statistical confidence interval applies. Result must not be promoted to hard-real-time, physical-device, X-server-stall, cross-platform or production safety claims.

## Stop

Stop after the first frozen formal result + independent audit. Runtime/live transfer requires a new Issue/lease.
