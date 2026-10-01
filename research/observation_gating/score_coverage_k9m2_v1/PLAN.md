# #4356: score calibration versus candidate-set coverage

Allocation: `score-coverage-4356-20260925-01`.
Intake main: `4a1f3957e91b412a64769199f78f2c4b0102d28b`.
Only `research/observation_gating/score_coverage_k9m2_v1/**` on
`research/score-coverage-20260925-k9m2` is owned.

## Scope and H / T / D / C / U

H: Separate nominal95% coordinate intervals need not give95% winner retention.
Calibrating a maximum residual yields a different vector-coverage contract, with
larger candidate sets. Amplitude shift can invalidate the calibration premise.
This is a synthetic statistical/software validation, not a new algorithm or
calibration of an actual detector. #4276's implication is preserved. #4339's
shared-affine mathematical model, #2751's budget/model study and #2466's live
dwell calibration are separate; no historical allocation is rerun.

T: Seeds4356101/4356102/4356103, exactly999 calibration +1000 IID +1000 shifted
rows each. Each truth vector is a uniform random permutation of[3,2,1,0]. Each
coordinate draws a retained uniform integer0..99; values0..2 add10 in calibration
and IID, or30 in SHIFTED_AMPLITUDE. Stream = Random(seed*10+split), split0/1/2;
shuffle precedes four randrange calls. All draws/truth/scores/sets are retained.
Only calibration truth reaches calibrate(); predict() receives scores/radii only.
Two interval policies keep the same possible-max rule; TOP1_POINT is a diagnostic
comparator, not an interval or confidence certificate. PRNG/runtime identities
are fixed. No package installation, GUI/model/provider/OS input or experiment
network. Provided Linux container, not an attested Docker/OrbStack image.

D: First raw data must include2997 calibration +6000 evaluation rows, all sources,
actual process returncode0, no timeout, and separate audit/control receipts.
Every seed's four MARGINAL95 IID coordinate counts must be>=950/1000; pooled
MARGINAL95 IID winner misses>150/3000; JOINT95 IID winner misses0; JOINT95 IID
set-size sum greater than MARGINAL95; SHIFTED JOINT95 winner misses>150/3000.
Every actually jointly covered row must retain the true maximum. All12 effective
copied-data mutations must reject normally; no no-op or crashing control counts.
All gates -> PASS_SCORE_COVERAGE_BOUNDARY_SYNTHETIC. A complete valid observation
without the stochastic discriminator -> HOLD_DISCRIMINATOR_NOT_EXPOSED. Algorithm
contradiction -> FAIL; missing source/raw/process/control evidence -> HOLD/STOP.
Do not tune thresholds/seeds/corpus after outcomes. Rerun/replacement/pooling0.

C: Rare positive errors deliberately expose a known multiplicity failure; the
result is not a natural workload estimate. JOINT95 may return all candidates,
so coverage alone is not useful pruning or adoption. Its rank guarantee is
marginal over calibration plus test, not conditional on every realized calibration
sample or input. Shift deliberately violates exchangeability. No generalization
from three fixed pseudorandom seeds to real apps; they are descriptive blocks.

U: Real detector quality, nonstationarity detection, learned score quality,
model interpretation, candidate-inspection cost, tokens/latency and task/runtime
promotion remain unknown. Integer arithmetic gives exact decisions, not zero
physical/model uncertainty. No calibrated metrological standard uncertainty or
coverage factor is invented; sampling uncertainty belongs to the declared
synthetic probability model. Same-author separate algorithm is not human review.

## Variable table (all score/count quantities are dimensionless, SI unit1)

| Symbol | Meaning | SI | Definition | Domain / condition | Type |
|---|---|---|---|---|---|
| K | candidate count |1|4|fixed|integer scalar|
| i,j | candidate index |1|coordinate identifier|0..K-1|integer scalar|
| n | calibration count |1|999 per seed|n>=19|integer scalar|
| alpha | nominal miscoverage |1|1/20|0<alpha<1|probability scalar|
| k | calibration rank |1|ceil((n+1)(1-alpha))|1<=k<=n|integer scalar|
| z_i | latent score |1|permuted3,2,1,0|scorer-only in evaluation|integer scalar|
| s_i | observed score |1|z_i+error|integer|integer scalar|
| q_i | interval radius |1|marginal or shared calibrated quantile|nonnegative|integer scalar|
| L_i,U_i | interval endpoints |1|s_i-q_i,s_i+q_i|L_i<=U_i|scalar pair|
| C | possible-max set |1|indices whose upper reaches all lower endpoints|subset of indices|finite set|
| t | true winning index |1|unique index with z_t=3|one per row|integer scalar|
| r_l | calibration nonconformity |1|coordinate absolute error or vector-max error|l=1..n|scalar|
| q | shared radius |1|kth calibration row-max residual|nonnegative|scalar|
| R | randomly tie-broken test rank |1|rank among n+1 exchangeable residuals|1..n+1|random integer|
| p | positive-outlier probability |1|3/100|model assumption|probability|
| E_i | coordinate covered event |1|L_i<=z_i<=U_i|measured or modeled|event|
| P | probability law |1|declared iid population, not empirical percentage|exchangeability where used|measure|

Dimensional check: endpoints subtract/add score quantities of unit1. Rank and
coverage compare counts/probabilities only. Clock values in execution receipts
are nanoseconds, never mixed with scores or used as performance gates.

## Analytical reduction before measurement

1. Set construction and its exact conditional implication:
   C = {i: U_i >= max_j L_j}. If all E_i hold and t maximizes truth, then for
   every j: U_t>=z_t>=z_j>=L_j. Thus U_t>=max_j L_j and t belongs to C.
   If U_i<max_j L_j, choose j attaining that maximum. For every feasible score
   vector z_i<=U_i<L_j<=z_j, so i cannot be maximal. Conversely, when U_i is at
   least every lower endpoint, choosing z_i=U_i and every other z_j=L_j witnesses
   i as a (possibly tied) maximum in the Cartesian-box contract. This does not
   impose #4339's shared constraints. Auditor independently uses this endpoint
   construction rather than the candidate's maximum-lower implementation.

2. Marginal coverage does not identify joint coverage. By the union bound,
   P(not all E_i)<=sum_i P(not E_i)<=K*alpha, hence
   P(t in C)>=P(all E_i)>=1-K*alpha (clipped at0).
   For K4/alpha0.05 this is only0.80, not0.95. No independence assumption is
   needed for this bound. It is a lower bound, not an estimate of actual misses.

3. Split-conformal rank: conditional on a fixed predictor, assume calibration
   and one future residual are exchangeable. Attach independent continuous tie
   breakers solely for this proof; symmetry makes each test rank R equally likely
   in1..n+1. If R<=k, at most k-1 calibration residuals precede the test, so the
   test value is no larger than the kth calibration value q. Therefore
   P(test residual<=q)>=P(R<=k)=k/(n+1)>=1-alpha. Ties make the unrandomized
   interval conservative. Here k950/n999. Applying this to the scalar row-max
   absolute residual makes test residual<=q exactly simultaneous containment of
   all four coordinates; step1 then ensures winner retention. Coordinate-wise
   independence is unnecessary, but exchangeability across rows is essential.
   This is not a conditional-on-the-fitted-sample guarantee.

4. Exact conditional counterexample law, not a measured result: when separate
   calibration radii are all0, each coordinate covers with probability1-p=0.97.
   The true winner is retained if it has the +10 error (probability p), or if
   no coordinate has the error (probability(1-p)^4). In the first case its higher
   latent score beats every other +10 score; in the second scores are exact.
   Otherwise at least one distractor exceeds the unperturbed winner. The events
   are disjoint, so retention=p+(1-p)^4=0.91529281 and misses=0.08470719.
   Joint containment is(1-p)^4=0.88529281. These apply conditional on the observed
   all-zero calibration radii, not to every random calibration dataset.

5. When shared q=10, every IID coordinate is covered and every candidate stays:
   upper endpoints are>=10 while all lower endpoints are<=3. Thus retention1
   comes with set size4. After a +30 amplitude shift, any perturbed lower endpoint
   is>=20 and every unperturbed upper is<=13. Exactly as in step4, the true winner
   is lost precisely when it is unperturbed and a distractor is perturbed. This
   yields the same conditional0.08470719 misses and exposes the exchangeability
   limitation, not a violation of the rank theorem. Thresholds are measured from
   calibration; no radius is forced to0 or10 by the implementation.

## Execution / audit / stopping

Public readable sources, this plan, CONFIG, ENVIRONMENT, excluded construction
receipt and FREEZE hashes precede formal. Exactly one `python -S -B execute.py`;
child timeout30s, outer container budget45s. Execute refuses an existing formal01
path. Run audit.py and controls.py in separate bounded processes, saving stdout,
stderr, actual returncode and command. Read-only verification may be repeated;
run.py/execute.py may not be rerun. Source tree rehash must remain exact afterward.
An artifact's existence or CI green is not a substitute for the original receipts.

Roadmap: construction -> source freeze/readback -> one synthetic allocation ->
raw audit/12 controls -> full additive PR -> exact-head relevant CI and review ->
qualified evidence merge/readback. Keep broad #4276/#18/#2751/#2789/ROADMAP open.
No automatic production threshold, GUI promotion or branch deletion is authorized
by a scoped result. Delete only an owned merged/dependency-free ref if supported.

## Primary background

Angelopoulos & Bates, A Gentle Introduction to Conformal Prediction and
Distribution-Free Uncertainty Quantification, arXiv:2107.07511v6.
Barber, Candes, Ramdas & Tibshirani, Conformal prediction beyond exchangeability,
arXiv:2202.13415v5.
Python3.13 standard-library random documentation. The seeded finite execution is
implementation evidence, not a new proof of the published statistical methods.
