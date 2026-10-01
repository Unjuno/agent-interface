# Issue #5424 T3 — freeze-induced selective labels

Allocation: `error-budget-selective-labels-5424-t3-20261001-01`  
Preregistered current-main publication base: `49db21e330768800e8b3486203b70306f4e402f6`  
Repository path: `research/analysis/action_class_error_budget_5424_t3_v1/`  
Branch: `research/5424-selective-labels-t3-20261001`

## H / T / D / C / U

- **H:** In a frozen-route trace, a quiet-window rule can infer recovery from zero executed outcomes even though every missing route outcome is censored. Requiring an authenticated positive repair probe bound to the current route generation avoids that specific false unfreeze, at the cost of remaining frozen on a missed/absent probe.
- **T:** Deterministic synthetic trace, 5 scenarios × 4 policies × 8 offered-task steps = 160 policy rows. Policies: `QUIET_WINDOW`, `FIXED_COOLDOWN`, `AUTHENTIC_CURRENT_PROBE`, and `HOLD_NO_PROBE`. Scenarios: unrepaired route/no primary exposure; repaired route/current-generation positive signal; repaired route/missed signal; stale-generation positive signal; and a common-cause outage affecting primary and fallback. Retain every offered task, fixture-only potential outcome, route execution/censoring, signal identity/generation, fallback result, and policy decision. Latent outcomes for frozen routes are oracle-only inputs; the policy-observed outcome must remain `UNKNOWN/CENSORED`.
- **D:** `PASS_METHOD_SCOPED` only if (1) a quiet-window unfreeze occurs in at least one unrepaired/no-exposure case and is flagged unsupported; (2) the authenticated-probe policy unfreezes only on positive, current-generation evidence; (3) absent/missed/stale evidence keeps that route frozen; (4) every executed fallback severe outcome remains in the combined exposure accounting; (5) no censored route outcome is labeled success; (6) an independently authored raw-only auditor reconstructs all rows/summaries and rejects four frozen corruptions: censor-to-success, dropped fallback severe event, stale-signal acceptance, omitted offered task. Otherwise preserve FAIL/HOLD.
- **C:** A verified native repair signal may be unavailable or correlated; a fixed cooldown may suffice for a known repair process; strict HOLD may sacrifice all primary-route progress. This T3 cannot select a deployable unfreeze policy.
- **U:** Fixture-authored deterministic method evidence only. No probabilities, calibration, causal harm reduction, deployed route attribution, GUI behavior, production SLO, or safety guarantee.

## Frozen procedure

Host-only CPython standard library because this task has no Docker allocation. No Docker CLI/daemon, runtime, model, GUI, user data, real route, or side-effecting action. Freeze `PLAN.md`, `fixtures.json`, `candidate.py`, `audit.py`, and `freeze.py`; perform syntax/source-integrity checks only; run the candidate exactly once; then run the separate auditor exactly once. No tuning, replacement, or retry. Preserve the first outcome.

The candidate and auditor are separately implemented. The auditor does not import candidate code; it replays the frozen fixture and separately validates rows, summaries, censor labels, current-generation probe binding, fallback counts, and all mutation controls.

Prior #5424 T0/T1/T2 artifacts, PR #5438, and their raw results/audits remain unchanged. This extension tests selective missing outcomes caused by the freeze itself; it does not rerun the burn-rate comparison or estimate real route rates.
