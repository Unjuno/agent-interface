# Issue #8319 A03 — raw-only factorial contrast analysis

## Frozen question and scope

This successor computes the paired contrasts already specified in Issue #8319 from the immutable A01 raw record. It does **not** rerun the candidate or either prior audit and does not change their dispositions.

- A01 candidate allocation: `8072-UPDATE-RULE-FACTORIAL-8319-A01-20261007`; original disposition remains `HOLD_AUDITOR_GATE_FAILURE`.
- A02 independent raw audit: Issue #8327; `PASS_AUDIT_ONLY`, 400/400 reconstructed rows, 6/6 mutations rejected.
- Input: `inputs/a01_candidate.json`, copied unchanged from A01 candidate raw; expected SHA-256 `ecffd8121a289d3533c94373c8f7aba50d9c349ffd5db534e46db16522897e9d`.
- Source base: current `main` `8bb0beb8bfdb93deb42f1c5e999ae7f22e934612`.
- Allocation: `8072-FACTORIAL-ANALYSIS-8319-A03-20261008`.

## H / T / D / C / U

- **H:** The full-versus-controlled feedback contrast in development accuracy, fresh-cohort accuracy, and optimism varies by update rule in this finite authored 100-seed factorial. No broad researcher-feedback effect is presumed.
- **T:** Read the exact frozen A01 raw once. Report all four cell summaries; seed-paired `FULL - CONTROLLED` contrasts within each updater; seed-paired `CASE_PATCH - STRATUM_PATCH` contrasts within each feedback mode; and the paired difference-in-differences. Report exact finite distributions (mean, median, range, sign counts). Do not rerun candidate or prior auditors; no p-values or population inference.
- **D:** `PASS_ANALYSIS_SCOPED` only if SHA-256 matches, all 400 rows map uniquely to 100 seeds × four cells, frozen cohort/safety/query invariants hold, and the independent raw-only auditor reproduces every cell/contrast and rejects all analysis mutations. Any mismatch is retained as FAIL/STOP; no retry.
- **C:** Issue #8327 already verifies raw record consistency; this analysis adds the paired estimands, not another integrity claim. The authored update rules may not represent human researcher behavior.
- **U:** No inference about actual researchers, real feedback policy, generalization, GUI behavior, privacy, product, or safety. The original A01 HOLD and A02 PASS_AUDIT_ONLY remain unchanged.

## Execution boundary

Pure finite standard-library CPU analysis. Issue #8319 explicitly states no container is required for this scope; this native run makes no isolation claim. Candidate count is zero in A03. The analyzer and independently implemented auditor are frozen before their respective single invocations. See `REPORT.md` and `RUN_RECORD.json` for outcomes.
