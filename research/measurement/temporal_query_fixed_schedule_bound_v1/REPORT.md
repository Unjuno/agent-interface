# #1633 Temporal fixed-schedule analytic bound

Decision: **PASS_TEMPORAL_FIXED_SCHEDULE_ANALYTIC_BOUND_SCOPED**

## Theorem 1 — four-slot incompatibility

Let a fixed schedule S contain at most four timestamps.

RECENT_DENSE requires at least four members of S in [900,1000]. Therefore every slot of a satisfying four-slot schedule lies in [900,1000]. LONG_BASELINE requires at least one member <=300 and at least one member >=900. The <=300 member lies outside [900,1000], so any LONG_BASELINE-satisfying schedule must devote at least one slot outside the RECENT_DENSE interval. Hence no four-slot fixed schedule can satisfy both relations. Therefore no fixed four-slot schedule can have positive score on all four preregistered request classes.

## Exact finite result

Grid: {0,25,...,1000} ms (41 points). Budget: 4. Anchors: {250,275,...,825} ms (24 anchors).

All C(41,4)=101,270 fixed schedules were enumerated exactly with Fraction arithmetic.

- schedules enumerated: 101,270
- schedules with positive coverage in all four classes: 0
- minimax class coverage: 0
- maximum equal-class average coverage: 43/96 = 44.7916666667%
- unique optimal fixed schedule: (300,475,650,900) ms

For that optimum the class scores are RECENT_DENSE=0, LONG_BASELINE=1, EVENT_CENTERED=4/24=1/6, REVERSAL_BRACKET=15/24=5/8. Their equal-weight average is 43/96.

A request-conditioned selector constructs valid <=4-frame schedules for RECENT_DENSE, LONG_BASELINE, and every one of the 24 EVENT_CENTERED plus 24 REVERSAL_BRACKET anchors: 50/50 constructions pass on the same source grid.

## Interpretation

This removes the narrow explanation that #1501's fixed comparator happened to use a poor schedule. Under the frozen four-frame relation contract, no universal fixed schedule can cover every later-revealed request class, and even the globally optimal fixed schedule reaches only 43/96 average relation coverage on the complete no-drop grid. Query adaptivity has a structural information-allocation advantage under this contract.

This is not a model-quality result. A frontier model may not benefit from the extra relation coverage; real request weights may differ; larger image budgets can change the bound; continuation/tool cost is absent here. Any Rung2 model experiment must therefore test model usefulness separately while keeping source capability and total image budget matched.
