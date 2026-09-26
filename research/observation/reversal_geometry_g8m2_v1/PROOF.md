# Conditional continuous-time feasibility proof

## Variables and units

|Symbol|意味|SI / internal unit|Definition|Domain and assumptions|Type|
|---|---|---|---|---|---|
|i,j|観測番号|1|newest=0, previous=1, oldest=2|{0,1,2}|integer scalar|
|t_i|元観測相対時刻|s|(source_ns_i-source_ns_0)/10^9|t_2<t_1<t_0=0; exact common clock|rational scalar|
|y_i|観測位置|px (not SI)|exact rational value of retained binary64 position|finite|rational scalar|
|x(t)|真の位置|px (not SI)|latent continuous trajectory|known speed and at most one reversal|real-valued function|
|v|速度の絶対値|px/s|73|known positive|rational scalar|
|epsilon|位置誤差上限|px|1|abs(y_i-x(t_i))<=epsilon|rational scalar|
|d|最新観測時点の右側方向|1|-1 or +1|right-hand velocity divided by v at t=0|integer scalar|
|tau|反転時刻|s|single reversal time|[t_2,0]; outside-history cases covered by constants|real scalar|
|c|反転地点または直線の切片|px|unknown absolute position|real, unconstrained a priori|real scalar|
|s_i|反転の前後符号|1|sign of t_i-tau in a fixed segment|{-1,+1}; endpoint formulas agree|integer scalar|
|a_i|反転時刻の係数|px/s|-d*v*s_i|fixed in each segment|rational scalar|
|b_i|固定位置項|px|d*v*s_i*t_i|fixed in each segment|rational scalar|
|L_i,U_i|許される切片の下限・上限|px|y_i +/- epsilon -a_i*tau-b_i|L_i uses minus; U_i plus|affine functions|
|D|実現可能な方向集合|1|all d with at least one compatible world|subset of {-1,+1}|finite set|

Pixels have no assumed conversion to metres; there is no physical-world distance claim. Time uses seconds in the proof; integer nanoseconds are divided by 10^9 exactly. Consequently v*(t_i-t_j), y_i-y_j and epsilon all have px units.

## Model and completeness

A constant-motion world has x(t)=c+d*v*t. A one-reversal world has x(t)=c+d*v*abs(t-tau). Before tau its velocity is -d*v; afterward it is d*v. A reversal at or before the oldest observation is observationally constant over the retained interval and has the constant world's newest direction. A reversal after the newest observation does not affect the queried direction at t=0 and is likewise covered by a constant world. A reversal exactly at t=0 is included with right-hand direction d. Thus constants and tau in [t_2,0] exhaust the declared family for this query. This is not a claim for arbitrary acceleration or multiple reversals.

Constant feasibility is immediate: each observation requires c in [y_i-epsilon-d*v*t_i, y_i+epsilon-d*v*t_i]. Their intersection is nonempty exactly when the largest lower endpoint is no greater than the smallest upper endpoint. This is necessary and sufficient, not merely a pairwise heuristic on displacements.

For reversal worlds, partition tau into [t_2,t_1] and [t_1,0]. Each absolute value is affine on each closed segment. At a segment endpoint t_i=tau both sign formulas give zero, so endpoint inclusion does not create a false world. In a fixed segment x(t_i)=c+a_i*tau+b_i.

The observation bound is equivalent to L_i(tau)<=c<=U_i(tau). A common c exists exactly when max_i L_i(tau)<=min_j U_j(tau), equivalently L_i(tau)<=U_j(tau) for every ordered pair (i,j). Substitution yields

(a_j-a_i)*tau <= y_j-y_i+2*epsilon+b_i-b_j.

Both sides have units px: (px/s)*s=px. For a positive coefficient this restricts tau from above, for a negative coefficient from below, and a zero coefficient requires its right-hand side nonnegative. Intersect all these half-lines with the current time segment. A nonempty intersection is therefore equivalent to feasibility, including equality boundaries.

The candidate takes any tau in that intersection and any c between the resulting max lower and min upper bounds. It explicitly checks the resulting complete trajectory against all three observations with exact rational arithmetic. The two time segments and constants are all examined for both directions. Hence its returned D is exact for rational observations/timestamps, and it supplies a concrete witness for every direction in D. Feasibility over real tau is not approximated by a grid: all inequalities have rational coefficients, and a nonempty interval with rational endpoints contains a rational witness.

## Independent oracle

The auditor instead retains both unknowns (c,tau). It forms six observation half-planes plus two segment-end half-planes. The feasible set is closed and bounded: tau is bounded by the segment, and any observation bounds c when tau is bounded. A nonempty bounded polygon, including a line segment or point, has a vertex at the intersection of two independent boundary lines. If there were no independent active constraints, a feasible point could move in an unconstrained line direction, contradicting boundedness. Therefore enumeration of all pairwise nonparallel line intersections with an all-half-plane membership test is necessary and sufficient. Constants are checked independently by interval intersection. This oracle does not import the candidate's elimination routine.

## Soundness of abstention

By the model/error assumptions, the true world's direction belongs to D. If D contains exactly one direction, that direction must be the true one. If D contains both, two explicit allowed worlds give the same three observations but opposite newest directions. Any deterministic estimator receiving only those observations must give the same answer in both worlds; any nonzero answer is wrong in one. UNKNOWN is therefore required for a universal direction claim in this model, not necessarily for a different task utility objective. Empty D means model-inconsistent observations, not a proof of either direction.

## Limit and decision relevance

A recent sample does not imply an informative inter-sample displacement. When the nominal travel across an interval is small relative to the error envelope, both signs may be compatible. Treating that ambiguity as a missing full-speed interval can differ from eliminating all feasible worlds. The formal finite matrix checks the exact published heuristic against this model; no historical numerical outcomes are overwritten.

The proof has no conclusion about direction after t=0, sensing calibration, authenticated timestamps, scene identity, task effects, latency or input authority. A conservative set can be too ambiguous for useful control. Count UNKNOWN and lost correct proposals explicitly rather than interpreting fewer wrong proposals alone as a task improvement.

## ERROR CHECK

Family coverage includes constants, within-window reversals and segment endpoints. One common offset is enforced across all observations. Time is continuous; no reversal-time discretization or post-result epsilon is used. Pixel/second dimensions are consistent. Binary64 observations are interpreted exactly; pre-observation physical uncertainty remains an assumption, not measured evidence.
