# Issue #5890 — successor allocation 02 preregistration

Status: frozen for a deterministic host-CPU method test; no candidate result is implied.

Allocation `PORTFOLIO-MULTIPLICITY-5890-T0-20261001-02`; additive GitHub path `research/analysis/portfolio_multiplicity_5890_t0_v2_20261001/`; branch `research/portfolio-multiplicity-5890-t0-20261001-r2`. Main base at freeze: `3d6ffc76d535309cf3820ed33cb9327354f03648`. Successor to allocation-01, which stopped before any candidate invocation because main advanced at its start gate. Allocation-01, branch r1, and all prior records remain unchanged.

## H / T / D / C / U

**H.** In a frozen synthetic stream, unadjusted per-claim promotion produces a larger false-discovery fraction than a prospectively ordered alpha-spending procedure for eligible independent tests; a type/dependency-aware ledger refuses calibrated statistical claims for deterministic methods, descriptive-only outcomes, a correlated copied p-value, hard safety failures, HOLD, and STOP.

**T.** Standard-library Python only, seed `58901002`, 32 portfolios × 13 claims = 416 rows. Each family contains 3 valid null tests, 3 valid alternatives, 1 ineligible correlated null with a copied p-value, a deterministic method PASS, method FAIL, descriptive outcome, HOLD, hard safety failure carrying a deliberately tiny/tempting p-value, and STOP. Null p-values use conservative integer quantization of domain-separated SHA-256 draws; alternatives use the preregistered `U^5` transform. Registered-order alpha spending is `0.05/[i(i+1)]` over valid statistical tests only; completion order is a separate coprime permutation and cannot affect the decision order. Candidate emits raw rows plus summaries; independent raw-only auditor reconstructs all 416 rows, p-value provenance, alpha decisions, and metrics, and rejects seven frozen corruptions: omitted failure, duplicate row, reordered start, shared-cohort relabel, post-hoc family relabel, invented method p-value, and forged safety status.

**D.** `PASS_METHOD_SCOPED` only if all 416 rows reconcile; eligible counts are 96 null, 96 alternative, and 32 ineligible correlated; global procedure promotes no null; fixed-seed naive FDP is strictly greater than online FDP; every ineligible category receives no calibrated promotion; safety failure is never promoted despite its small p-value; all seven corruption controls reject. Otherwise preserve FAIL/STOP without retry. This one seeded portfolio is descriptive only, not an FDR guarantee.

**C.** Hash-derived p-values, truth labels, and outcomes are authored synthetic data. The alpha-spending claim relies on valid super-uniform null p-values and registered order; shared model/task/scorer dependence is represented only by an intentionally ineligible copied-p case. No model, task, GUI, runtime, or empirical study is represented.

**U.** No empirical false-discovery rate, interface superiority, product benefit, safety qualification, or release decision follows. Real portfolios require prospective claim registration, evidence validity, defensible family/dependence mapping, and suitable error-control assumptions. A hard safety gate remains non-compensable.

## Execution and resource boundary

Issue #5890 allocation-01's recorded Docker/storage STOP is not reused. This allocation uses a small host-local CPython run only; it does not claim Docker evidence or inherit another task's container/GPU/resource reservation. The configured Docker contexts exist but their daemon API had stalled in this task. No network, GUI, model, or external input is used.

Run the construction suite before freezing. Then record hashes of `runner.py`, `audit.py`, `test_multiplicity.py`, and this preregistration in `FREEZE.json` before the single candidate invocation. Candidate once; separate raw-only audit once only after candidate exit 0. Do not rerun either under this allocation ID.

