# Issue #6100 — feasibility-gated coalition attribution T0

**Disposition: `PASS_METHOD_SCOPED` for authored finite potential-outcome tables only.** This validates exact bookkeeping, feasibility gates and mutation rejection. It is not empirical mechanism attribution or evidence of an Agent Interface route effect.

## H / T / D / C / U

- **H:** Exact coalition tables distinguish additivity and positive/negative 2-factor interaction, while only a 3-factor context interaction reverses the baseline-only A/B ranking relative to Shapley. Infeasible coalitions remain missing/HOLD; correctness/effect, safety, latency and tokens are not collapsed.
- **T:** Five fixed cases, 23 feasible coalition arms, 20 attempt rows per arm (460 total). Four complete families (three 2-factor plus one 3-factor) and one 2-factor family missing the B-only coalition. Candidate uses attempt-level reported outcomes; an independent raw-only auditor checks frozen oracle labels, arm feasibility/completeness, all endpoint summaries, interactions and Shapley values.
- **D:** `PASS_METHOD_SCOPED`: audit errors=0; 9/9 tests pass. Additive interaction=0, positive interaction=+1/10, negative interaction=−1/20. The three-factor example has baseline A=4/20 > B=3/20 but Shapley A=3/20 < B=11/40; C=1/8 and allocations sum to full value 11/20. All complete 2-factor families satisfy the identity `φA−φB = v(A)−v(B)`. The missing-B-only family remains `HOLD_NO_FEASIBLE_FACTORIAL` with no Shapley allocation. Four planned mutations and one latency mutation are rejected.
- **C:** All potential outcomes are authored integers divided by 20 attempts. The sole scalar characteristic function is task-effect success rate. Safety events, mean latency and mean tokens remain separately reported vector coordinates; none is a Shapley utility input. No inferential uncertainty is estimated.
- **U:** No model, app, GUI, mechanism intervention, randomized population, causal identification, task outcome, safety finding, route benefit, or transferable/intrinsic mechanism value. Shapley only decomposes the specified synthetic table; T1 would require feasible, comparable, independently scored live configurations and allocation authority.

## Frozen example results

| Case | Factors | Feasible arms | Interaction / ranking | Disposition |
|---|---|---:|---|---|
| Additive | 2 | 4/4 | interaction 0; A and B allocations equal their baseline marginals | Analyze |
| Positive interaction | 2 | 4/4 | +1/10 | Analyze |
| Negative interaction | 2 | 4/4 | −1/20 | Analyze |
| Context-dependent reversal | 3 | 8/8 | baseline A>B; Shapley B>A; A=3/20, B=11/40, C=1/8 | Analyze |
| Missing B-only arm | 2 | 3/4 | B-only is infeasible, not zero; no Shapley output | `HOLD_NO_FEASIBLE_FACTORIAL` |

For the 2-factor families, the exact identity means Shapley cannot reverse the baseline-only A/B rank. The 3-factor table is the arithmetic example posted in the Issue correction; all values here are scaled by the 20-attempt denominator.

## Construction history and provenance

Preparation/freeze base: main `b63fe0812e5816163105bdf37384c5f1dd407760`. Source/protocol/test digests, image digest, engine and platform are in `FREEZE.json`.

An initial pre-freeze mutation suite found that two corrupt tables caused the auditor to raise `KeyError` during incomplete-coalition Shapley recomputation. The 5-case/23-arm construction raw and passing baseline audit are retained; the auditor was hardened to skip attribution when the feasible-arm map is incomplete, and the full mutation suite then passed 9/9 before freeze. This is a construction robustness failure, not a scientific FAIL or official frozen run.

Official run: OrbStack Docker Engine 29.4.0, Linux ARM64, pinned `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `--network=none`. Candidate, independent raw audit, identical frozen-source repeat, tests and `py_compile` all succeeded. The two official raw files are byte-identical. `SHA256SUMS` covers source, freeze, protocol, report, all raw/audit outputs and construction disclosure.
