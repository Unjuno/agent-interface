# Shared-score possible maxima: #4339

## Scope, hypothesis and decision

This is analytical research plus finite executable contract verification, not a GUI,
model, detector-calibration or population experiment. Preserve #4276's marginal
interval PASS and #4146's tie result. The marginal comparator is conservative, not
incorrect. The changed information is a declared common affine parameter. Do not
use this new information when a producer cannot justify the joint model.

H: intersection of all winning inequalities for one shared scalar returns exactly
all feasible maximizers, including ties and zero-width feasible intervals. Marginal
intervals can include impossible winners; pairwise existential checks can also
include a candidate whose opponent-specific witnesses cannot coexist.

T: CPython standard-library exact Fraction arithmetic. The input corpus comprises
1458 grid cases: all six ordered intercept/slope coefficients in {-1,0,1}, each
with residual radii (0,0,0) and (0,1,0), parameter interval [-1,1]. The12 additional
cases are declared in corpus.py: common offset, incompatible pairwise witnesses,
interior singleton, both endpoint ties, constant tie, independent residuals,
one candidate, rational crossing, point domain, heterogeneous four-candidate
residuals and large exact integers. Total1470. Inputs are generated and hash-frozen
before execution; no full-corpus candidate run occurs before the public freeze.
Construction uses numerically disjoint small examples in test_maxima.py.

Compare MARGINAL_BOX, PAIRWISE_POSSIBLE and SHARED_WITNESS on the same inputs.
Candidate uses half-line intersection. Raw-only auditor imports no candidate,
runner or corpus generator; it examines exact affine crossing points plus both
domain endpoints with the favorable residual assignment for each nominated winner.
See PROOF.md for completeness of this alternative algorithm.

D: PASS_SHARED_SCORE_MAXIMA_CONTRACT requires all1470 exact records, matching
source/input identities and actual exit0, reference equality for all memberships
and feasible intervals, nonempty output, joint contained in pairwise contained in
box, common-offset and incompatible-pairwise discriminators, preserved singleton
feasibility, action_authority=false and task_success=null. All10 declared effective
copied-record controls must reject without a no-op or audit exception. Missing
source/coverage/process evidence is HOLD/STOP; a complete contradiction is FAIL.
No threshold optimization or favorable-case selection is permitted.

C: only one shared scalar plus independently selectable box residuals is covered.
The joint model is authored, not fitted or validated against real detections.
Smaller exact sets under additional assumptions are not a measured attention,
time, token, task-success or runtime benefit. The common-offset countermodel in
PROOF.md demonstrates why unverified dependence must not be assumed. The separate
algorithm has the same author and shares Python Fraction; it is not independent
human review or a second arithmetic backend.

U: multidimensional/nonlinear/cross-residual dependence, calibration error,
source authenticity, real detector performance, model interpretation, efficient
implementation tradeoffs and production integration remain unknown. No physical
combined uncertainty or coverage factor is estimated; exact arithmetic only
removes rounding from the declared rational contract.

## Allocation and evidence

One retained invocation: `python -S -B supervise.py retained`. The supervisor
refuses an existing output directory and records exact stdout/stderr, PID, argv,
wall-clock brackets and exit. No case rerun, replacement, exclusion, pooling or
post-result tuning. Timing is diagnostic, not a benchmark.

Afterwards, run only raw audit and copied-record controls:

    python -S -B audit.py retained
    python -S -B controls.py retained

Retain source, all inputs/outputs, subprocess receipt, original audit, exact
mutation paths/before/after values and their rejection reasons. The complete raw
JSON may be losslessly compressed for GitHub, but must be decoded and hash-checked.
`verify.py` performs read-only reconstruction and imports no candidate or runner.
Never call run.py merely to reproduce published evidence.

## Coordination and roadmap

Intake main46e85863a9d0bfa9f5b7648fd81f3423907ca106. Read main, README,
CURRENT_GOAL active section, ROADMAP, recent open/closed Issues, open PRs,
first100 branch names, #4276 and both comments. Targeted shared/correlated/affine
Issue/PR/branch searches returned no exact owner. Searches are bounded/non-atomic;
unpublished work remains unknown. #4335/#4336 and every foreign path are excluded.
Blocked historical sources in #4334/#4337, #4331/#4333 and #4322 are not reused.

Owned branch: research/shared-score-maxima-20260925-q2v9.
Owned path: research/analysis/shared_score_maxima_q2v9_v1/** only.
No shared runtime/workflow/index or historical result is changed.

Roadmap: proof and construction -> public exact source/gate freeze/readback ->
one retained finite verification -> raw audit and10 effective controls -> complete
evidence PR -> exact-head applicable CI and scoped review -> qualified research-
evidence merge/readback -> preserve dependencies; delete only an owned ref when
a supported operation and dependency evidence permit. Global ROADMAP, #4276,
#18 and #2751 are not completed by this study.
