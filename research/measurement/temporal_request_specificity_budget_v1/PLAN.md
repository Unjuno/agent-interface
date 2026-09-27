# #1648 Temporal request-specificity budget lattice

TASK: `TEMPORAL-REQUEST-SPECIFICITY-BUDGET-LATTICE-20260918-001`

Parents: #1633 and #1640. This successor keeps the exact grid `T={0,25,...,1000}`, anchors `A={250,275,...,825}`, and relation predicates unchanged. It changes only how much request information is available before sample selection.

## H
Minimum sample budgets under the frozen relation family form the lattice:

| Request information | RECENT | LONG | EVENT | REVERSAL | equal-class mean |
|---|---:|---:|---:|---:|---:|
| none | universal minimum 11 | — | — | — | — |
| class only | 4 | 2 | 8 | 6 | 5 |
| class + anchor | 4 | 2 | 2 | 2 | 5/2 |

## Analytical reduction

EVENT over all anchors is equivalent to hitting every consecutive 4-grid-point window from 150 through 925 ms. Eight pairwise-disjoint genuine windows give a lower bound of 8; an 8-point witness gives the matching upper bound.

REVERSAL over all anchors is equivalent to hitting every consecutive 6-grid-point window from 100 through 975 ms. Six pairwise-disjoint genuine windows give a lower bound of 6; a 6-point witness gives the matching upper bound.

For a fixed anchor, EVENT left/right regions are disjoint and REVERSAL left/right regions are disjoint, so each needs at least two points; `(a-25,a+25)` is a two-point witness for both.

RECENT needs four points by predicate cardinality. LONG needs two because `<=300` and `>=900` are disjoint required regions.

The #1640 universal 11-point lower-bound certificate and witness are independently rechecked from constants.

## T
One deterministic analytical formal invocation after source freeze. Exact-set verification of certificates/witnesses, all 24 anchors for both anchored classes, independent auditor, and corruption controls. No GUI/X11/model/provider/network/task input/shared runtime.

## D
PASS only if universal=11, class-only minima exactly `{4,2,8,6}`, class+anchor minima exactly `{4,2,2,2}`, means exactly `5` and `5/2`, all certificates are genuine/disjoint, all matching witnesses validate, independent audit passes, all corruption controls reject, and formal1/reruns0/replacements0/tuning0.

## C
The theorem concerns information allocation on this discrete relation family. Continuous acquisition, approximate relation tolerance, nonuniform class priors, query overhead, or inability of a model to exploit returned frames can change practical value.

## U / stop
No model quality, token, latency, GUI, human-tempo or runtime-promotion claim. Stop after the first deterministic result and audit. Any later model study is a separate empirical successor.
