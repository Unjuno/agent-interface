# Issue #7955 — observation choice over a finite likelihood set, T0 A01

## Disposition

`PASS_METHOD_SCOPED` and `H_PASS_SCOPED` for the frozen, finite synthetic
decision problem. The study distinguishes a fixed-measure VOI envelope from a
separately named minimax-regret fallback. It does not validate a deployment
credal set, detect unmodeled distribution shift, or establish a live GUI
policy.

## H/T/D/C/U

- **H:** A point-estimate decision-value policy can choose a check whose value
  is lower under another likelihood model still admitted by the credal set.
  Fixed-measure VOI envelopes should identify the model-dependent ranking; a
  separately frozen fallback should reduce worst-case regret in the reversal
  case without changing singleton or invariant controls.
- **T:** [`model.json`](model.json) freezes two hidden states, two safe routes,
  two check options, balanced prior, calibration counts, finite likelihood
  sets, costs, dependency/freshness/safety metadata, and in-set or out-of-set
  evaluation truths before the formal run. Likelihoods are symmetric binary
  channels: for accuracy `a`, `P(+|ready)=a`, `P(+|not_ready)=1-a`, with
  negative-outcome probabilities as complements. Enumerate all model/check/
  outcome combinations; compare point-model VOI, cost-only, information gain,
  fixed-measure envelopes, and an explicit minimax-regret fallback on envelope
  overlap/reversal. An independent direct enumerator recomputes posteriors,
  route choices, values, gates, envelopes and regrets.
- **D:** `PASS_METHOD_SCOPED` requires exact independent reconstruction,
  invariant rankings only when one check's lower VOI exceeds every rival's
  upper VOI, `UNCERTAIN_MODEL_DEPENDENT_RANKING` on overlapping/reversed
  intervals, and no selection of hard-gated, dependent or stale checks.
  `H_PASS_SCOPED` requires lower worst-case in-set regret in the reversal case
  and unchanged cost/regret in singleton and invariant controls. The outside-
  set control is reported separately and cannot be used as evidence that the
  envelope detects misspecification.
- **C:** The point-model mismatch may instead call for better calibration or
  shift detection. A conservative fixed route or simpler cost-only policy may
  suffice. A wide credal set can make selection uninformative.
- **U:** All probabilities, values, costs and model sets are small authored
  fixtures. No model-set coverage, GUI likelihood, user value, live task effect,
  authorization, runtime behavior or end-to-end benefit is measured.

## Frozen model and method boundaries

The primary source explicitly separates rule-specific values under an
imprecision-handling rule from the envelope of classical single-measure VOI
across admissible measures; those are not interchangeable. This experiment
computes the envelope first. Only after an overlapping/reversed ranking does
it invoke the distinct minimax-regret fallback. It does not substitute a
Γ-maximin VOI and label it an envelope. See Iskandar's [finite-credal-set VOI
preprint](https://arxiv.org/abs/2607.06570) and Chen, Choi & Darwiche's
[decision-robustness VOI paper](https://ojs.aaai.org/index.php/AAAI/article/view/9684).
Those works establish methods in their own settings; they do not validate this
GUI transfer or the chosen model bounds.

The six frozen cases are: singleton calibration; multiple models with a
strictly invariant ranking; a rank reversal; a point likelihood with the
evaluation truth outside its singleton set; dependency, stale-epoch and
hard-gate controls; and a case with no admissible checks. The three controls
forbidden in the gate case are deliberately more attractive by cost or
accuracy, so a failure to filter them is visible. The all-inadmissible case
must return `UNKNOWN_NO_ADMISSIBLE_CHECK` and select nothing.

Each likelihood set is centered on a frozen balanced calibration sample (100
observations per hidden state). Additional endpoint values are predeclared
sensitivity scenarios, not confidence intervals or statistically derived
coverage guarantees. All hypothesis claims are conditional on these authored
finite sets.

On the reversal case, point-model VOI, cost-only and information gain select
`check_A`; fixed-measure intervals overlap (`A=[0.6,3.8]`, `B=[1.3,3.3]`),
so the method emits `UNCERTAIN_MODEL_DEPENDENT_RANKING`. Its separate
minimax-regret fallback selects `check_B`. Worst-case regret over the frozen
in-set models falls from `2.7` for the point arm to `2.5`; singleton and
invariant controls remain at zero regret with the same selected check and
cost. Thus the hypothesis passes narrowly in these authored cases.

The limitation control is material: when the declared credal set is the
singleton point model but the evaluation truth lies outside it, the method
still reports an invariant ranking and selects `check_A`; its regret against
the true-model oracle is `2.7`. The envelope cannot detect a truth excluded
from its model set. This is a demonstrated boundary, not hidden distribution
shift detection.

## Reproduction and audit

The frozen formal command is `python3 -B run_candidate.py`; it launches the
candidate once and retains stdout as `result.json`, plus exit/byte-hash
metadata in `terminal.json`. Then run `python3 -B audit.py`. The auditor reads
the frozen inputs and retained output without importing candidate code.

The final audit independently checked 6 cases, 22 finite likelihood models,
41 model/check value rows, and 22 evaluation truths, including both outcomes
for every assessed check. It passed the method and in-set hypothesis gates.
The detailed machine-readable audit is in `audit.json`; candidate output is in
`result.json`.

## Execution scope

This finite CPU-only T0 ran as one local Python process on macOS (Python
3.14.5, arm64). The candidate used no network, GUI, model, input device or user
data. No container or formal isolated-runtime claim is made. Construction
preflights occurred before the freeze while the implementation/auditor were
being debugged; only the separately frozen launch recorded in `terminal.json`
is the experiment result. `CONSTRUCTION_PREFLIGHT.json` preserves one
unfrozen development output and is excluded from the formal decision.

## Source identities

See [`FROZEN.json`](FROZEN.json) for the exact base revision, command, runtime,
and SHA-256 identities. `result.json` and `audit.json` are derived evidence and
are hashed in `terminal.json` and `audit.json`, respectively.
