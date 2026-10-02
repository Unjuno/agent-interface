# Issue #6451 T0 — cutoff-local causal audit method

## Disposition

**STOP_RAW_OUTPUT_NOT_RETAINED.** One formal candidate invocation exited 0, but its JSON stdout was truncated by the command-output transport before a complete raw artifact could be retained. The independent auditor was therefore not run. No PASS/FAIL on the six-case method hypothesis is claimed; retries are zero.

Construction uncovered a real estimator pitfall: an unadjusted one-distance contrast falsely produced a 6-unit jump in the zero-effect smooth-trend case. The frozen local-linear symmetric-distance estimator recovered zero and the planted 2-unit effect on the valid fixtures. Source inspection also shows the field named `naive_near_cutoff_difference` is computed over all observations, not only the frozen bandwidth; because the complete formal raw was lost, that comparison was not independently adjudicated and this is an additional reason not to claim PASS. Construction tests also cover refusal cases, fuzzy first-stage, raw reconstruction and four corruption mutations. These tests are not the formal result.

## H / T / D / C / U

- **H:** At a frozen assignment cutoff, local analysis with identification-refusal gates can distinguish a planted local guard effect from smooth age trends and refuse sorting, coincident transition and timestamp-heaping cases.
- **T0:** Six finite no-model cases: valid sharp cutoff; smooth trend/zero effect; sorting/bunching; coincident focus/app transition; coarse timestamp heaping; treatment noncompliance. Compare a naive near-cutoff contrast with cutoff-local linear contrast; an independent raw-only audit reconstructs assignments, denominators and rejection reasons. No GUI, model or container allocation.
- **D:** `METHOD_PASS_SCOPED` only if valid sharp effect is recovered within tolerance, smooth zero-effect trend is not called a gain, sorting/coincident transition/heaping are refused, and noncompliance reports its first stage without overclaim. Any missing raw attempt or false causal PASS is FAIL/STOP.
- **C:** Stipulated potential outcomes and a tiny deterministic fixture do not establish RD validity on observed routes; an ordinary randomized comparison may be simpler and more useful.
- **U:** No live GUI threshold, optional guard eligibility, causal treatment effect, safety, product or global policy claim. The separate T1 eligibility gate remains closed.

## Provenance and attempted execution

- Intake main commit: `67ebd3016af9ed99a5cb40a39d4d753871f51d75`.
- Frozen source/fixture/test hashes and expected decisions: `FREEZE.json`.
- Construction suite: 6 methods passed on CPython 3.12.10, Windows 11 x86_64; `py_compile` passed. Standard library only.
- Formal command: `python candidate.py cases.json` (with the frozen absolute paths in the local work directory). Candidate invocation 1, exit 0, no retry.
- Complete stdout was not captured; no candidate SHA can be stated. Auditor invocation 0. Exact STOP machine record: `STOP.json`.
- No WSL, WSLc, Docker Desktop, GUI, model, network, or external action was used for this T0.

## Limits / next step

Do not rerun this consumed one-shot allocation. Preserve this STOP unchanged. Any further method validation requires an additive successor with a runner that streams candidate output to a retained file and independently verifies the complete byte count/hash before auditor invocation. T1 remains unauthorized absent a separately evidenced eligible threshold and collision-free owner allocation.
