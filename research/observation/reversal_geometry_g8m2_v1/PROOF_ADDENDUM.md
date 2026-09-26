# Postformal proof clarification: existence of an enumerated vertex

This clarification strengthens the independent-oracle paragraph of the frozen PROOF.md. The informal sentence about moving in an unconstrained direction should not be read as claiming that any locally feasible motion is globally unbounded. That implication alone is invalid. No source, input, first output, decision gate or archived proof is changed, and no scientific allocation is rerun.

## Variables

| Symbol | Meaning / 意味 | Unit | Definition / domain | Type |
|---|---|---|---|---|
| c | unknown position offset / 位置切片 | px, not SI | finite real | scalar |
| tau | reversal time / 反転時刻 | s | in one closed sample-time segment | scalar |
| P | feasible offset/time pairs / 実現可能集合 | mixed coordinates | closed bounded intersection of the eight affine half-planes in the frozen oracle | subset of R^2 |
| q | selected lexicographic minimum / 辞書式最小点 | (px,s) | minimum c in P, then minimum tau among minimizers | ordered pair |
| u | perturbation direction / 摂動方向 | (px,s) | nonzero vector tangent to every active boundary at q | vector |
| delta | perturbation magnitude / 摂動係数 | 1 | sufficiently small positive real | scalar |

## Complete argument

Assume P is nonempty. It is compact because it is closed and bounded. The continuous c coordinate therefore attains its minimum. The subset of minimizers is itself nonempty and compact; the continuous tau coordinate also attains its minimum on that subset. Select q by these two successive minimizations.

Suppose the active boundary normals at q span fewer than two dimensions. There is a nonzero u tangent to every active boundary. All inactive inequalities have strictly positive slack at q. Because there are only finitely many inactive inequalities, delta can be chosen positive and small enough that both q+delta*u and q-delta*u still satisfy every inactive inequality. Active inequalities remain equalities by tangency. Both perturbed points are therefore in P.

If the c component of u is nonzero, one of those points has smaller c, contradicting the first minimization. If that component is zero, its tau component must be nonzero; one point then has the same c and smaller tau, contradicting the second minimization. Thus the active normals span two dimensions. Two active boundaries have linearly independent normals and meet at q. The auditor enumerates that pair and will test q against every half-plane.

This proves that every nonempty bounded feasible set in this problem, including a segment or singleton, contains an enumerated feasible intersection. Conversely, any enumerated intersection satisfying all half-planes is by definition feasible. Together these establish exact equivalence of the vertex oracle and feasibility without requiring P to have nonempty interior.

## Unit and scope check

Perturbations are coordinatewise: delta is dimensionless, so each sum preserves the original position and time units. The rank argument can equivalently be made after scaling c by1px and tau by1s. It makes no physical pixel-to-metre claim and adds no stochastic assumptions. This is a proof clarification only; all frozen numerical results and source hashes remain unchanged.
