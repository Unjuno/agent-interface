# Shared-score possible-max contract: proof and limitations

## Variables and units

All scores and latent parameters here are dimensionless mathematical quantities,
not calibrated physical measurements or probabilities.

| Symbol | Meaning (Japanese) | SI unit | Definition | Domain/assumption | Type |
|---|---|---|---|---|---|
| n | 候補数 | 1 | number of candidates | integer1..8 in implementation | scalar integer |
| i,j | 候補添字 | 1 | candidate indices | 0..n-1 | scalar integer |
| a_i | 基準スコア | 1 | declared intercept | rational implementation input | scalar |
| b_i | 共通変数への感度 | 1 | declared affine slope | rational | scalar |
| e_i | 独立残差の上限 | 1 | absolute residual bound | nonnegative rational | scalar |
| r_i | 候補固有残差 | 1 | independent free residual | [-e_i,e_i] | scalar real |
| t | 全候補が共有する不確定変数 | 1 | same parameter for every score | [l,u] | scalar real |
| l,u | 共通変数の下限・上限 | 1 | domain endpoints | rational, l<=u | scalar pair |
| z_i | 許容された実現スコア | 1 | a_i+b_i*t+r_i | joint model required | scalar real |
| L_i,U_i | 周辺スコア下限・上限 | 1 | extrema of z_i ignoring cross-score dependence | L_i<=U_i | scalar pair |
| c_ij | 勝敗差の定数項 | 1 | a_i-a_j+e_i+e_j | i!=j | scalar |
| d_ij | 勝敗差の傾き | 1 | b_i-b_j | i!=j | scalar |
| F_i | 候補iが最大になれる共通変数集合 | 1 | intersection below | closed interval or empty | set |
| C_J | 共同実現可能な最大候補集合 | 1 | {i:F_i nonempty} | subset of indices | finite set |
| C_P | 相手ごとに実現可能な候補集合 | 1 | each opponent can be beaten, not necessarily at same t | subset | finite set |
| C_B | 周辺区間での可能最大集合 | 1 | {i:U_i>=max_j L_j} | subset | finite set |

## 1. Exact elimination of independent residuals

The model is z_i=a_i+b_i*t+r_i, with one shared t in [l,u] and independent
residuals r_i in [-e_i,e_i]. Candidate i is a possible maximizer when there exists
one simultaneous (t,r_0,...,r_(n-1)) for which z_i>=z_j for every j. Ties count.

Necessity: suppose such a realization exists. Since r_i<=e_i and r_j>=-e_j,

    a_i+b_i*t+e_i >= z_i >= z_j >= a_j+b_j*t-e_j.

Thus c_ij+d_ij*t>=0 for every j!=i.

Sufficiency: suppose one t satisfies all those inequalities. Choose r_i=e_i and
r_j=-e_j for every j!=i. Independence of the box residuals makes this one joint
assignment legal. The inequalities then give z_i>=z_j simultaneously. Therefore

    F_i = [l,u] intersect {t:c_ij+d_ij*t>=0 for every j!=i}
    C_J = {i:F_i is nonempty}.

This proof fails if residuals have extra joint constraints. Independent residual
boxes are not interchangeable with arbitrary correlated errors.

## 2. Exact interval-intersection implementation

Each opponent contributes precisely one condition:

    d_ij>0: t >= -c_ij/d_ij
    d_ij<0: t <= -c_ij/d_ij
    d_ij=0 and c_ij>=0: all t
    d_ij=0 and c_ij<0: no t.

Start with [l,u]. Intersect the lower or upper closed half-line for each opponent,
or mark the intersection empty for the last case. After each step the retained
interval equals the intersection processed so far, by the definition of set
intersection. By induction over the n-1 opponents, the final interval is exactly
F_i. If its lower endpoint equals its upper endpoint it remains nonempty; rejecting
that case would incorrectly remove a feasible tie. If lower exceeds upper it is
empty. The single-candidate case has no constraints and returns [l,u].

A midpoint of any nonempty returned interval is a rational witness, together with
the residual assignment above. For exact rational inputs every bound and comparison
is rational. Fraction integer/string construction avoids binary-float conversion.
The loop performs quadratic many pair comparisons; no runtime timing improvement
is claimed and arbitrary-precision arithmetic cost is not constant.

## 3. Independent crossing-point oracle is complete

For each nominated i form shifted intercepts a_i+e_i for i, and a_j-e_j for j!=i.
The oracle considers both domain endpoints and every pairwise crossing of these
shifted affine lines that lies in [l,u]. It directly evaluates all scores at each
of these exact points and retains those at which i reaches the maximum.

If a nonempty F_i touches a domain endpoint, that endpoint is tested. Otherwise,
its lower and upper endpoints must be boundaries of one of the defining nonconstant
linear inequalities: without an active boundary, the finite collection of strict
inequalities would allow a small extension, contradicting extremality. Such a
boundary is an equality between i and an opponent, hence a crossing in the oracle's
set. Singleton intervals have the same property. Constant equal lines create no
missing boundary; they constrain neither endpoint. Thus a nonempty F_i has at least
one tested witness and all its extreme endpoints are tested. Conversely every
tested winner satisfies all inequalities and belongs to F_i. The minimum and
maximum accepted test points are exactly its endpoints. This oracle does not
approximate the real parameter continuum by a uniform grid.

## 4. Containment and meaning of the comparators

If one t beats all opponents, each opponent individually admits such a t, so
C_J is contained in C_P. If i can beat each j at some t, then U_i>=L_j for every j,
so C_P is contained in C_B. Therefore

    C_J subseteq C_P subseteq C_B.

Every true maximizer of every model-valid realization belongs to C_J by section1.
A member of C_J is possible, not certain. Set reduction relies on ADDITIONAL
joint-model information; it is not a fair assertion that the marginal rule was
wrong given its own weaker input contract.

Example1: a=(2,1,0), b=(4,4,4), e=(0,0,0), t in [-1,1]. Scores keep the same order
for every t, so C_J={0}. Marginals are [-2,6],[-3,5],[-4,4]; C_B={0,1,2}.

Example2: a=(0,1,1), b=(0,1,-1), e=0, t in [-1,1]. Candidate0 beats candidate1
only at t=-1, and beats candidate2 only at t=1. Each pair has a witness, but those
witnesses cannot coexist. C_P={0,1,2}, C_J={1,2}. The term exists-t-for-each-j is
not the same quantifier order as exists-one-t-for-all-j.

Example3: a=(0,0,0), b=(0,1,-1), e=0, t in [-1,1]. Candidate0 is maximal only at
t=0, where all three tie. Its feasible interval [0,0] must be retained.

## 5. Countermodel: unjustified correlation can remove the real winner

Reuse Example1's marginal intervals but let actual scores be (-2,5,4). Each lies
in its stated marginal interval, and candidate1 wins. There is no common t giving
these scores under the zero-residual shared-offset model. C_J={0} would then omit
the winner; C_B includes it. This is deliberately OUTSIDE the new joint contract,
not a hidden failure or a proof that calibration exists. Without justified shared
coefficients and error bounds, use the marginal evidence or report unknown rather
than pruning according to an invented dependency.

## 6. Dimensional and uncertainty checks

All additions combine dimensionless scores; b_i*t has the same unit as a_i and
r_i. For nonzero d_ij, -c_ij/d_ij has the unit of t (here1). Only comparable
scores are ranked. Rational exactness removes implementation rounding in this
contract; it neither makes detector uncertainty zero nor supplies a calibrated
combined uncertainty, coverage factor, probability or real-world confidence.

ERROR CHECK: constant slopes, negative slopes, endpoints, zero-width domains,
interior singleton ties, independent residuals and one-candidate input are covered.
The score model, oracle completeness and containment are separately justified.
No model-viewing, action-authority or task-success conclusion follows.

## Primary background

L.H. de Figueiredo and J. Stolfi (2004), Affine Arithmetic: Concepts and Applications,
Numerical Algorithms37,147-158. DOI10.1023/B:NUMA.0000049462.70970.b6. Its abstract
explains tracking first-order dependencies; it does not validate this code or
establish real detector calibration. https://doi.org/10.1023/B:NUMA.0000049462.70970.b6

Python3.13 fractions documentation, exact rational construction:
https://docs.python.org/3.13/library/fractions.html
