# Issue #6225 T0 — pre-failure route diversification under hidden regimes

Allocation: `PREFailure-ROUTE-DIVERSIFICATION-6225-T0-HOST-20261002-01`

Disposition: **`METHOD_PASS_SCOPED`** (finite simulator/method gates only)

## H / T / D / C / U

- **H:** A bounded prospective route mixture may lower a predeclared session-tail endpoint when route A degrades under an unobservable regime and detection is delayed. This allocation does not test a real GUI, actual route equivalence, or a deployable policy.
- **T:** Exhaustive deterministic eight-task session-policy sequences. For each hidden/observable/shared-failure shock onset `1..6`, enumerate all 28 masks choosing exactly two of eight B slots; also run stable-A, B-idle-decay, route-induced queue-carryover, and no-eligible-B controls. Compare best-mean plus reactive fallback, context gating, the bounded mixture, a conservative-default allocation, and a regime oracle used only as an unattainable diagnostic. Every simulated policy sequence starts from a reset state and retains all eight offered tasks.
- **D:** Pass the scoped method only if an independent raw-only implementation exactly reconstructs the candidate, the hidden-shock tail improves inside the direct-cost budget, controls have their predeclared behavior, no safety gate is bypassed, the offered frame is complete, and all four mutation controls are rejected. The gates and simulator inputs were frozen in `FREEZE.json` before formal execution.
- **C:** Observable regime evidence should favor context gating; shared failures should defeat diversification; stable conditions should show no completion advantage for the mixture; queue carryover may add cost without improving task outcomes. Idle B readiness must decay to a typed no-effect yield, never be silently treated as ready.
- **U:** All route tables, latency, observation delay, assignment masks, and scenario frequencies are synthetic and deterministic. No uncertainty interval, natural regime frequency, actual safety rate, qualified route pair, or desktop effect can be inferred. A lower tail can trade against average completed tasks, and this result must not be promoted to a policy recommendation.

## Result

The separately implemented auditor reconstructed **2,970/2,970** complete policy-session records exactly. All **16/16** frozen gates passed; all four mutations were rejected.

In the hidden exogenous-shock family, the fraction of sessions with at least three unresolved tasks was **1.000** for best-mean plus reactive fallback and **0.857** for the bounded mixture. The mixture remained within the declared direct-cost budget (mean **1.362** units/task; limit **1.75**). But mean unresolved tasks were **3.232** under the mixture versus **3.000** under best-mean plus reactive fallback: the mixture improved this chosen tail threshold while reducing mean verified completion from `5.000/8` to about `4.768/8`. This trade-off is material; the result is a metric-specific method demonstration, not evidence that the mixture is preferable.

Controls behaved as frozen: when the shock was observable, context gating had tail fraction `0.000` versus mixture `0.857`; under common-mode route failure both policies averaged `5.5` unresolved tasks; the stable-A control had zero unresolved tasks in both and no completion gain for mixture. Stale B attempts yielded `YIELD_UNREADY` with `NO_EFFECT`; B was never called when ineligible. The conservative baseline stayed on A because B's declared `0.8` completion lower bound was below the `0.9` completion floor. The shared-queue control retained route-induced latency carryover. No forbidden effect was produced.

The hidden-shock result depends on the simulator's predeclared three-consecutive-unresolved reactive detector: a successful B task resets that detector. Thus mixture can postpone fallback and increase average unresolved obligations even as it modestly reduces the selected three-or-more tail. That sensitivity is explicit in the frozen rules and is a reason to keep the issue open, not tune this allocation after seeing results.

## Execution and audit

- Frozen source commit: `d51556de103bb780eacbe50862c30971820c466d` (base `14b81dd1f6853623a694266b98538f812847257a`).
- During integration, main advanced to `673763554192ae26636e07d5a48f03b3cd7fb044` (#6226). A changed-path comparison found no overlap with this additive analysis package; that exact main commit was merged before publication, preserving the frozen source commit unchanged.
- Candidate: `python -B candidate.py`, one formal invocation, exit 0; started `2026-10-01T20:01:17Z`; wrote `candidate.json` with 2,970 records.
- Independent auditor: `python -B auditor.py`, one formal invocation, exit 0; started `2026-10-01T20:01:27Z`; stdout `METHOD_PASS_SCOPED`.
- Formal retries, replacements, tuning, model calls, GUI calls, and live actions: zero.
- Construction-only suite: `python -B -m unittest -v test_method.py`, 5 tests passed. Its initial `FAIL_IMPORT` (test imported `audit` instead of `auditor`) and correction are preserved in `CONSTRUCTION.json`.
- Repository integration: `python -B research/analysis/check_index.py` passed with 350 retained result/failure directories; the existing analysis-index regression suites passed (8 tests for endogenous-demand rebound, 12 for selection-aware shadow audit). These checks did not rerun the frozen candidate or auditor.
- Host: Windows CPU, CPython 3.12.10. Docker Desktop service was stopped. Read-only `docker version` and `docker ps` probes did not return within the 10-second command window; Docker-related CLI/backend processes remained, so the shared Engine was not started, stopped, or cleaned up. The formal finite CPU test ran directly on the host; no container was used.
- Raw candidate output, independent audit, freeze, inputs, code, tests, source blob IDs and SHA-256 values are retained beside this report and summarized in `RUN.json`.

## Scope and disposition

This closes only the frozen no-model method rung for this authored simulator. It does **not** establish the empirical hypothesis, route qualification/equivalence, a real-system regime shift, independent GUI effect scoring, reliable B readiness, or a suitable correctness/cost trade-off. Do not randomize consequential user actions. Issue #6225 remains open for its read-only eligibility audit and any separately authorized, collision-free empirical allocation; if no eligible same-obligation pair/reset/effect oracle exists, record HOLD rather than infer from this synthetic result. No historical result is changed.
