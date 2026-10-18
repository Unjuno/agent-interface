# Issue #7889 T0 — frozen preregistration

**Allocation:** method-only synthetic T0; no model, GUI, app, OS input, repository runtime, or shared-resource allocation.
**Source main:** `f60752d0fb71595363a80977636ca74c1fd10b21`.
**Branch:** `research/7889-generalizability-budget-t0-a01-20261005`.
**Study path:** `research/analysis/generalizability_budget_7889_t0_a01_20261005/`.
**Image:** `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (`python:3.12-slim`, Linux/amd64).

## H/T/D/C/U

- **H:** With route-by-task and/or route-by-app heterogeneity, spending 96 paired observations mostly on repeats within a small set of cells gives lower probability of retaining a population route decision than spending the same count on more distinct tasks/apps. The result can be absent under a route-main-effect-only profile.
- **T:** Deterministic synthetic factorial experiment with known components and exact Gaussian decision probability. Compare 3×4×8 (repeat cells), 3×16×2 (more tasks within apps), and 8×6×2 (broader apps), each 96 observations. Scenarios: route main effect only; task interaction; app interaction; combined interactions. Separately enumerate a rare-hard-task stratum at p=.01. Validate a nested balanced method-of-moments estimator against known components and exact decision probability. Exercise malformed sparse/unbalanced and unknown-outcome inputs as fail-closed gates.
- **D:** PASS_METHOD_SCOPED only if mean component estimates are within 0.06 absolute of each planted variance component for the balanced profiles; exact decision probabilities are within 0.025 of empirical simulation frequencies; the route-main-only profile does not prefer broader designs by more than 0.04; both interaction profiles demonstrate at least one breadth design exceeding the repeat design by 0.10 probability; rare-hard-task exact coverage ranks repeated design last; every planted mutation is rejected/detected. Failure of a criterion is retained as FAIL_METHOD; invalid/missing facets return HOLD.
- **C:** Breadth need not improve a fixed route contrast when interactions are absent; convenience samples and misspecified families can make apparent components misleading.
- **U:** Normal continuous paired contrasts and this finite synthetic generator do not validate binary outcome models, actual task/app populations, assignment/carryover, effect scoring, uncertainty intervals for sparse facets, or prospective route decisions.

## Frozen generator and estimator

Each observation is a paired route difference `D_ats = beta + A_a + T_at + e_ats`, with independent zero-mean normal app-route, nested task-route, and residual terms. Main effect `beta=.60`, practical margin `.40`. Four variance profiles `(sigma2_app, sigma2_task, sigma2_error)` are `(0,0,.36)`, `(0,.64,.36)`, `(.64,0,.36)`, and `(.36,.64,.36)`. Exact variance of the population mean estimator is `sigma2_app/A + sigma2_task/(A*T) + sigma2_error/(A*T*S)`; exact decision probability is `Phi((beta-margin)/sqrt(var))`.

The balanced nested ANOVA estimator uses `MS_error`, `MS_task`, and `MS_app`: estimates are `MS_error`, `(MS_task-MS_error)/S`, and `(MS_app-MS_task)/(T*S)`. Negative method-of-moments estimates are retained in raw ledgers and are not silently truncated.

The rare-hard scenario samples each distinct task as hard with probability .01. Ordinary task contrast is +.5; hard is -4.0; population mean is .455 and practical margin is .40. The exact decision probability is binomial over distinct tasks only; repetitions do not create new task draws.

Malformed-cell controls remove one paired outcome or mark one outcome unknown. Required result is HOLD, never complete-case PASS. Mutations: count repeats as independent task draws; omit task interaction; pool away app effects; drop unknown outcomes; omit rare-hard stratum. The independent auditor independently recomputes hashes, design counts, exact probabilities, component targets, gates, and mutation expectations from the frozen inputs and raw ledgers.

## Execution sequence

1. Freeze source, preregistration, candidate, independent auditor, study input, command, image, host/container inventory, and SHA256 manifest before candidate execution.
2. Execute the candidate once in WSLc with `--pull never --network none --cpus 1`; no retry after a candidate invocation. Preserve exit code and complete stdout/stderr.
3. Only if candidate exit is zero, invoke the independent auditor once in a separate WSLc container against read-only frozen inputs and candidate outputs; no retry after auditor invocation.
4. Preserve all outcomes, including STOP/FAIL/HOLD, and report only the frozen claim scope.
