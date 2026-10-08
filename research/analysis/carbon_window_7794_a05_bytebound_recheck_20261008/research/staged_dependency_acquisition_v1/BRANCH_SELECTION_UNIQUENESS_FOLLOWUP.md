# Follow-up — branch selection must remain uniquely valid

Status: **REFINE retained candidate.** Revalidating only the selected branch's predicate truth is insufficient when another branch can become newly true before final admission.

## Question

The previous follow-up retained semantic branch-predicate revalidation rather than exact raw-value equality. This block asks a narrower question: is it enough that the originally selected branch is still true, or must final admission preserve the runtime's original *unique branch selection*?

The current compiled runtime rejects zero or multiple matching branches. Therefore ground truth here permits execution only if the originally selected branch remains the unique match.

## A — independent branch predicates

Two branches:

- A: `x >= 0`
- B: `y >= 0`

Plan states use exactly one matching branch. Initial `x,y ∈ [-3,3]`; final `x,y ∈ [-5,5]`: **2,904** scored transitions.

| revalidation | stale accepts | false rejects | correct |
|---|---:|---:|---:|
| selected branch predicate still true | **864** | 0 | 2,040 |
| exact raw `x,y` equality | 0 | **696** | 2,208 |
| **same branch remains unique match** | **0** | **0** | **2,904** |

The 864 failures occur when the selected branch remains true but the previously inactive branch also becomes true. Selected-truth revalidation would execute where the runtime's fresh branch selection should be ambiguous.

## B — mutually exclusive branches

Branches:

- A: `x < 0`
- B: `x >= 0`

77 scored transitions.

- selected-truth: 77/77 exact;
- unique-selection: 77/77 exact;
- exact raw equality: 32 false rejects.

Thus selected-predicate truth can be a valid simplification **when mutual exclusivity is independently guaranteed**.

## C — overlapping predicates on one variable

Branches:

- A: `x >= 0`
- B: `x <= 2`

Plan states begin where exactly one matches. 66 scored transitions.

- selected-truth: **18 stale accepts**;
- exact raw equality: **18 false rejects**;
- unique-selection: **66/66 exact**.

This shows the issue is overlap/branch-selection semantics, not merely use of two independent variables.

## Decision

Refine the final-admission dependency from merely `selected branch predicate truth` to a semantic **branch-selection identity**:

`BRANCH_SELECTION(state, selected_branch, unique=true)`

Final admission must establish that the same branch still uniquely matches before combining that evidence with selected-action dependencies.

Optimization is allowed only with proof obligations:

- if the branch set is independently proven mutually exclusive, preserving the selected branch predicate can imply unique selection;
- otherwise the branch-selection result must be recomputed/revalidated against competing branches.

Do not fall back to exact raw state equality; it is unnecessarily strict in both this block and the earlier predicate-truth block.

## H / T / D / C / U

**H.** Plan validity depends on preserving the unique branch-selection result, not merely truth of the selected branch predicate.

**T.** Exhaustive finite checks: 2,904 independent-predicate transitions + 77 mutually exclusive transitions + 66 overlapping-single-variable transitions.

**D.** PASS for unique-selection semantics in all 3,047 scored transitions. FAIL selected-truth as a general rule (882 stale accepts total across overlapping blocks). FAIL exact raw equality as a precision rule (746 false rejects total).

**C.** A compiler or authored contract may prove branches mutually exclusive and permit a cheaper selected-predicate check. That proof is separate evidence and must not be assumed from observed data alone.

**U.** Finite scalar predicates only; no exact runtime execution; no solver-backed proof of mutual exclusivity; no performance claim.

## Next gate

Issue #197 should test final admission using **unique branch-selection preservation + selected-action dependencies**. If the exact method's branch set is proven mutually exclusive, retain the proof and test the cheaper selected-predicate form as a separate optimization.
