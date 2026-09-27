# Logical release time from query brackets: conditional tight interval

This is a deterministic observation contract, not a new OS mechanism or a claim
about physical HID timestamps. Its execution check is finite and synthetic.

## Variables and assumptions

| Symbol | Meaning / 意味 | SI unit | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| a_d, z_d | DOWN照会の開始・返却時刻 | s | Clock readings bracketing the last DOWN query | Real, 0 <= a_d <= z_d; stored ns | scalar pair |
| a_u, z_u | UP照会の開始・返却時刻 | s | Clock readings bracketing the first subsequent UP query | Real, z_d <= a_u <= z_u; stored ns | scalar pair |
| q_d, q_u | 各照会の内部状態観測時刻 | s | The unknown snapshot instants | q_d in [a_d,z_d], q_u in [a_u,z_u] | real scalars |
| r | 論理DOWN→UP遷移時刻 | s | The unique release between the two states | One key, one server incarnation, no re-press/other writer | real scalar |
| D | 判定期限 | s | Declared comparison boundary | Same comparable monotonic clock domain | real scalar |
| I | 可能なrelease時刻の集合 | s-valued set | Projection of compatible snapshot/transition times | Exact-clock model below | interval |
| W | 区間幅 | s | z_u - a_d | Nonnegative; not calibrated uncertainty | real scalar |
| G | 有限検証の時刻グリッド | s-valued set | {10,...,18} ns | Synthetic arithmetic only | finite set |
| N | 有限入力数 | 1 | Number of ordered four-tuples drawn with replacement from 9 grid times | Fixed 495 | integer scalar |

The observed state is DOWN strictly before r and UP at and after r. The caller's
serial synchronous queries contain the internal snapshots. No server lifetime,
key identity, or clock-domain change is allowed. Absence of a detected re-press
is not independently sufficient to prove the no-re-press assumption. The live
construction fixes the single input program and checks all emissions; this is
not a general multi-owner history reconstruction.

## Proof: necessity

1. DOWN at q_d implies q_d < r by the state-transition definition.
2. UP at q_u implies r <= q_u.
3. Query bracketing gives a_d <= q_d and q_u <= z_u.
4. Combining those inequalities gives a_d < r <= z_u. Thus every compatible
   release belongs to I = (a_d, z_u]. The lower endpoint is open.

## Proof: sufficiency and sharpness

Take any proposed r satisfying a_d < r <= z_u. Choose q_d = a_d and q_u = z_u.
Both choices lie inside their respective query intervals. The proposed r gives
q_d < r <= q_u, so the first snapshot is DOWN and the second UP. This constructs
a compatible hidden history for every point in (a_d,z_u]. Consequently no strict
subset can be guaranteed from these two query brackets alone. Necessity and
sufficiency together establish the exact feasible interval.

When a_d = z_u, the proposed interval is empty: no exact-clock history satisfies
both observations. The correct output is UNKNOWN / incompatible evidence, never
a vacuous deadline certificate. For real finite-resolution clocks, an apparent
zero-width interval need not imply a physically impossible event; it still does
not support the strict exact-clock certificate without a clock-error model.

## Deadline logic and forbidden narrowing

For nonempty I, z_u <= D is sufficient for release by D, because every r in I is
at most z_u. It is also necessary for this evidence alone to guarantee r <= D:
when z_u > D, the compatible choice r = z_u violates the deadline.

An upper bound later than D is NOT by itself proof of late release. When I spans
D, both on-time and late histories are compatible. This implementation returns
UNRESOLVED_BOUND rather than certifying lateness. In the special case a_d >= D,
the entire interval is after D, but the helper does not implement that additional
late classification.

Using z_d as the lower endpoint is unjustified: release may follow the DOWN
snapshot but precede the DOWN response. Using a_u as the upper endpoint is also
unjustified: release may follow the UP request but precede its internal snapshot.
Example: DOWN bracket [10,18] ns, UP bracket [20,28] ns yields (10,28] ns.
A release at 12 ns and one at 25 ns each have compatible internal snapshots.
Neither narrowed interval (18,28] nor (10,20] covers all compatible histories.

## Unit and uncertainty check

Every endpoint, deadline and subtraction above has dimension time. W = z_u-a_d
is in seconds; an integer-ns width converts to seconds by division by 10^9.
Sample counts and input counts are dimensionless. No game ticks, PID values,
sequence numbers or image ages are added to clock times. Nanosecond storage and
advertised clock resolution are not nanosecond physical accuracy.

If query-clock errors are bounded only after calibration, the endpoints must be
expanded by those justified bounds before using this theorem. No such calibrated
bounds, combined standard uncertainty u_c, or coverage factor k are available in
this study. The exact arithmetic check is not a physical uncertainty estimate.

## Finite verification and its limit

Enumerate all a_d <= z_d <= a_u <= z_u from nine integer grid points. Counting
nondecreasing choices of four values gives binomial(9+4-1,4) = 495. For each,
an independent program enumerates every allowed q_d, q_u and integer r. There
are 9 empty cases (all endpoints equal) and 486 nonempty cases. The independent
oracle reconstructs the tight grid interval and checks both deliberately narrow
comparators on the same input. The continuous theorem above, not the finite grid,
justifies the continuous conclusion.

The original local construction helper omitted the nonempty-interval guard. It
is retained unchanged as a prototype control. A separately defined pure wrapper
rejects that case. This is not an allegation about the repository X11 backend
and does not change any prior GUI observation, outcome, or source.

## ERROR CHECK (logical)

The strict lower endpoint, equality at the deadline, empty interval, no-repress
assumption, same-server identity, monotonic clock comparability and logical-vs-
physical distinction are explicit. Release evidence grants neither task success
nor fresh input authority. Empirical audit results are reported separately.

## Primary background

X.Org Xlib specification, Keyboard State / XQueryKeymap: a 32-byte bit vector
reports logical key state, which can lag physical state when processing freezes.
https://www.x.org/releases/X11R7.6/doc/libX11/specs/libX11/libX11.html
Python 3.13 time documentation, monotonic / monotonic_ns:
https://docs.python.org/3.13/library/time.html
These define the observation/clock APIs; neither validates this local experiment.
