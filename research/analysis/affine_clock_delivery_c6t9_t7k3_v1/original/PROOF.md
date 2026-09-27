# Bounded affine-clock projection of a logical release interval

This is a conditional exact-arithmetic theorem and implementation verification,
not a physical-clock calibration, new clock-synchronization algorithm, empirical
latency benefit, or runtime safety certification. It extends the explicit clock
comparability assumption in retained r4m8 without changing its evidence.

## 1. Variable table / 変数表

| Symbol | 意味 | SI unit | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| s | 観測時計上の時刻、固定基準からの差 | s | Sensor-clock coordinate | real; possibly negative relative to reference | scalar |
| t | 期限時計上の対応時刻 | s | t = a s + b | same declared clock epoch and validity horizon | scalar |
| a | 二時計の進み方の比 | 1 | positive affine scale | a0 <= a <= a1; a0 > 0 | scalar |
| b | 二時計のオフセット | s | affine intercept | b0 <= b <= b1 | scalar |
| a0,a1 | 進み方の事前下限・上限 | 1 | externally justified input bounds | finite rational; 0 < a0 <= a1 | scalar pair |
| b0,b1 | オフセットの事前下限・上限 | s | externally justified input bounds | finite rational; b0 <= b1 | scalar pair |
| j,n | 校正条件番号・件数 | 1 | j = 1,...,n | 1 <= n <= 32 in implementation | integer scalars |
| s_j,p_j,q_j | 校正点と対応時刻の包含下限・上限 | s | p_j <= a s_j + b <= q_j | closed, finite bounds; justified, not midpoint assumptions | scalar triple |
| P | 全校正と事前境界を満たす時計集合 | mixed 1 and s coordinates | intersection of all stated linear inequalities in (a,b) | compact convex subset, possibly empty/line/point | 2D set |
| L,U | 観測時計の解放区間端点 | s | r in (L,U] | L < U; one transition, no re-press, valid source identity | scalar pair |
| r | 唯一の論理解放時刻 | s | sensor coordinate of DOWN -> UP | any real in (L,U] | scalar |
| D | 期限時計上の比較期限 | s | threshold for t <= D | finite rational input | scalar |
| m,M | 可能な期限時計時刻の下限・上限 | s | min_P(aL+b), max_P(aU+b) | defined only for nonempty P | scalar pair |
| ell_i,u_k | オフセットの下側・上側一次関数 | s | b0 and p_j-s_j a; b1 and q_j-s_j a | finite sets of affine lines | real functions |
| J | 実現可能な進み方の集合 | 1 | rates with max ell_i <= min u_k | closed interval, or empty | interval |
| g(s) | 期限時計の実際の対応関数 | s | used only in out-of-model example | need not be affine outside assumptions | function |
| i,k | 上下包絡線の番号 | 1 | indices of lower/upper affine lines | finite index sets | integers |
| a_l,b_l,a_u,b_u | 下限と上限を与える時計パラメータ | 1 for a; s for b | minimizer/maximizer in P | existence by compactness | scalar pairs |
| r_l | 下限に近い仮の解放時刻 | s | L < r_l <= U and a_l*r_l+b_l < y | chosen in sufficiency proof | scalar |
| y | 実現可能性を示す任意の対象時刻 | s | m < y <= M | arbitrary in claimed projection | scalar |
| f | 時計・解放時刻の変換 | s output | f(a,b,r)=ar+b | continuous on P x (L,U] | function |
| N | 合成入力数 | 1 | 3*3*6*6*4*7 + 16 | exactly 9088; no stochastic sampling | integer |

All time coordinates in the mathematical/synthetic corpus are seconds represented
by exact rational strings. They are not measured timestamps. Large rate ranges
are mathematical stress inputs, not estimates of real oscillator accuracy.
No standard uncertainty u_c or coverage factor k has been calibrated.

## 2. Preconditions and the old interval

The retained r4m8 theorem observes one logical DOWN snapshot within a synchronous
query bracket and a later UP snapshot within another. Under one release, no
re-press, the same key/server incarnation, comparable clocks and exact bracket
containment, it establishes precisely r in (L,U], where L is the last DOWN query
START and U is the first UP query RETURN. We accept that interval as an input;
this new program does not inspect keyboard state or construct an actuation.

The affine relation must hold throughout the entire declared source-time horizon,
including every calibration sample and (L,U]. Agreement at finitely many sample
points does not prove an affine clock between or beyond those points. The parser
requires an explicit horizon, matching clock/epoch identifiers, positive rate,
nonempty interval, finite rational values and at least one calibration constraint.
Identifier equality is not authentication; all input provenance remains assumed.

## 3. Exact feasible projection theorem

Assume all preconditions and P nonempty. Define m = min_P(aL+b) and
M = max_P(aU+b). Compactness of the bounded closed P and continuity ensure both
extrema are attained.

### Necessity, including strictness

Take any feasible clock (a,b) and any r in (L,U]. Since a >= a0 > 0,

    m <= aL+b < ar+b <= aU+b <= M.

Therefore every possible target-clock release lies in (m,M]. The lower endpoint
can NEVER be reached: even a clock minimizing aL+b has ar+b greater than it.
The upper endpoint is attained by a maximizer of aU+b with r=U.
Nonemptiness follows as well: for any feasible clock aU+b > aL+b >= m, hence M>m.

### Sufficiency and sharpness: every point is possible

Fix any y with m < y <= M. Let (a_l,b_l) minimize aL+b and let (a_u,b_u)
maximize aU+b. Choose r_l sufficiently close to but greater than L so that

    L < r_l <= U and a_l*r_l+b_l < y.

Such a choice exists because a_l is finite/positive and y-m>0. The two points
(a_l,b_l,r_l) and (a_u,b_u,U) belong to P x (L,U]. Their line segment belongs
to that set because P is convex and every interpolated release coordinate is
strictly greater than L and at most U. The function f(a,b,r)=ar+b is continuous
on that segment, with initial value below y and terminal value M >= y.
The intermediate value theorem supplies a point on the segment with f=y.
Thus every y in (m,M] is realizable. No smaller set can be guaranteed from this
contract. This proves both endpoints, openness and the exact projection.

### Empty calibration or release evidence

If P is empty, the assumptions contradict one another. If L>=U, the input release
interval is not a valid instance of the theorem. Neither condition may produce a
vacuous ON_TIME or LATE certificate: return UNKNOWN_INCONSISTENT or UNKNOWN_INVALID.
Neither status alone identifies which upstream observation was wrong.

## 4. Exact deadline trichotomy

For a valid nonempty interval (m,M]:

- ON_TIME iff M <= D. Sufficiency follows from every t<=M. If M>D, the feasible
  attained endpoint M itself contradicts universal on-time release.
- LATE iff m >= D. When m=D, strict t>m is crucial: all releases are strictly
  after D. When m>D the conclusion is immediate. Conversely, if m<D, choose any
  y strictly between m and min(D,M), or M when appropriate; Section 3 provides
  a feasible on-time release. Universal lateness is therefore not justified.
- Otherwise m<D<M. Both an on-time point and the late endpoint M are possible,
  so return UNRESOLVED.

These statuses are statements about all feasible histories in the declared model,
not task success, permission, real-time enforcement or a new actuation lease.

## 5. Candidate algorithm and its completeness

For fixed a, each calibration condition is equivalent to

    p_j - s_j a <= b <= q_j - s_j a.

Include b0 among lower lines ell_i and b1 among upper lines u_k. A feasible b
exists iff max_i ell_i(a) <= min_k u_k(a), equivalently ell_i(a)<=u_k(a) for
EVERY lower/upper pair. Each pair gives a scalar half-line or all/none of the real
line. Intersect these half-lines with [a0,a1]. The result J is exactly the feasible
rate interval; no pairwise clock witness is substituted for their simultaneous
intersection. This elimination also handles J reduced to a single point.

For a in J, minimizing aL+b selects b=max_i ell_i(a), while maximizing aU+b
selects b=min_k u_k(a). Hence the two objectives become a piecewise-linear upper
envelope for the minimum and a piecewise-linear lower envelope for the maximum.
On each interval between consecutive line-intersection coordinates, their active
line cannot change, so the objective is affine there. An affine function attains
its minimum and maximum at interval endpoints, unless constant, in which case
both endpoints still attain the optimum. Therefore it suffices to evaluate J's
endpoints and every relevant line intersection inside J. Identical/parallel lines
have no new crossing; tied optima are handled without a numerical tolerance.
All operations use exact rational arithmetic.

The method is elementary one-variable elimination and affine-envelope optimization,
not a claimed new optimization method.

## 6. Independently structured oracle

The auditor builds all two-dimensional half-planes directly, enumerates pairwise
intersections of their boundary lines with nonzero determinant and retains every
intersection satisfying ALL inequalities. It then evaluates aL+b and aU+b at
those vertices. It never imports or calls the candidate elimination/envelope code.

Why vertices suffice: for a nonempty compact polygon, a linear objective attains
an extremum. If an extremizer lies in the interior, the objective is either
constant or movement along its gradient improves it until a boundary is reached.
On a nontrivial boundary segment the same argument moves to an endpoint or the
objective stays constant to that endpoint. A bounded one-dimensional feasible
set has endpoints; a zero-dimensional set is its single point. At every such
endpoint/point at least two linearly independent active boundary normals must
exist, otherwise there is an unbounded direction or a non-extreme segment through
it. Such points occur among the enumerated pairwise boundary intersections.
The rectangle constraints guarantee boundedness, including degenerate cases.

The finite program checks an exact continuous-polytope optimum for EACH synthetic
input. It is not a grid over hidden clock parameters. The universal result rests
on the proof, not on interpreting finite test counts as a reliability probability.

## 7. Comparators and explicit counterexample

MARGINAL_BOX independently bounds the feasible a and b coordinates and optimizes
on their Cartesian product. This product contains P, so its interval contains the
exact projection: it cannot justify a contradictory definite conclusion, but can
lose decision power when rate and offset are coupled.

NOMINAL_POINT selects one feasible clock: the midpoint of J and the midpoint of
its allowed b-section. Feasibility of that chosen clock does not make its release
interval a bound for every possible clock. It is deliberately a point estimate,
not alleged deployed runtime logic.

Example: a in [1,2], b in [-10,0], and the calibration t=10 at s=10 imply
b=10-10a. The release input (11,12] maps exactly to (11,14]. The nominal clock
(a,b)=(3/2,-5) maps it to (23/2,13]. Thus deadline13 is UNRESOLVED, although the
nominal comparator says ON_TIME. At deadline14 the exact result is ON_TIME,
whereas the independent marginal box (1,24] remains UNRESOLVED. At deadline11,
the strict lower endpoint makes the exact result LATE.

## 8. Non-affine limit, not hidden by the PASS

Take declared a=1,b=0, samples at s=0 and s=2 with exact t=s, and release input
(0,1] with deadline1. The declared affine model certifies ON_TIME. A strictly
increasing, continuous alternative actual clock can pass both calibration points
while mapping s=1 to1.5: set g(s)=1.5s on [0,1] and g(s)=0.5s+1 on [1,2].
It agrees at0 and2, but release at1 occurs at controller-time1.5, after deadline1.
Therefore even two exact calibration samples and clock monotonicity do not prove
an affine model or its rate bounds between samples. This is OUT_OF_MODEL, not a
candidate implementation failure and not physical evidence of clock behavior.

## 9. Dimensional and error check

a is dimensionless; a*s, b, the calibration bounds, endpoints and D all have time
units. Eliminating a divides a time bound by a time coefficient, yielding a
dimensionless rate bound. No PID, event count or clock epoch is added to time.
Exact Fraction arithmetic removes numerical rounding in this model, NOT physical
measurement error. Declared bounds, epoch/horizon validity, timing containment,
non-affine drift and actual measurement provenance dominate unquantified error.
No u_c/k or confidence interval is fabricated. CPU scheduling affects execution
cost, not these exact rational outputs. Boundary, singleton, empty and invalid
cases are covered by tests; new empirical results are reported separately.

## Primary background

Python3.13 time documentation: https://docs.python.org/3.13/library/time.html
Python3.13 fractions: https://docs.python.org/3.13/library/fractions.html
RFC5905: https://www.rfc-editor.org/rfc/rfc5905
These describe clock/numeric background; none validates this new implementation.
Same-host Python monotonic clocks are shared across processes. Merely starting
another local process does not require inventing a different clock offset.
