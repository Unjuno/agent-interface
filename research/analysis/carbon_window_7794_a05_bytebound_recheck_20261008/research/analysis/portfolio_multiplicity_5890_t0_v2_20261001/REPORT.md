# Issue #5890 successor T0 — portfolio multiplicity ledger

Disposition: **PASS_METHOD_SCOPED**. This is one deterministic synthetic stream only; it establishes no empirical FDR bound, interface superiority, or safety qualification.

## H / T / D / C / U

**H.** An ordered type/dependency-aware ledger can restrict calibrated promotion to eligible statistical claims and a declared global alpha-spending rule, while preventing local unadjusted selections from erasing the family denominator or bypassing deterministic/safety outcomes.

**T.** Frozen allocation `PORTFOLIO-MULTIPLICITY-5890-T0-20261001-02`, main base `3d6ffc76d535309cf3820ed33cb9327354f03648`, seed `58901002`, 32 synthetic portfolios × 13 claim rows = 416. CPython 3.12.10 on Windows, standard library only. The five-test construction suite passed and `py_compile` passed before source freeze. `FREEZE.json` records candidate/auditor invocation counts as zero and source hashes before the formal run. The candidate ran once and exited 0; a separate raw-only auditor ran once and exited 0. No Docker container, network, model, GUI, game, or input was used.

**D.** `PASS_METHOD_SCOPED`. The auditor independently reconstructed 416/416 rows: 96 valid null tests, 96 alternatives, 32 correlated/ineligible copied-p tests, and 32 each of method PASS, method FAIL, descriptive, HOLD, hard-safety-failure, and STOP. Under unadjusted per-claim p<.05, the fixed stream promoted 2 null and 49 alternative claims (FDP 2/51 = 0.0392157). Registered-order alpha spending `alpha_i=0.05/[i(i+1)]` promoted 0 null and 11 alternative claims (FDP 0/11 = 0). The seven independent mutation controls all rejected: omitted failure, duplicate, reordered start, shared-cohort relabel, post-hoc family relabel, invented method p-value, and forged safety status. Every hard-safety row carries a nominally tempting p-value `1e-6` but is ineligible and none promoted. No non-statistical or correlated row received a calibrated promotion.

These are fixed-seed descriptive counts, not an estimate or guarantee of an error rate. The global rule is a conservative sequential alpha-spending procedure under the simulated valid-test assumptions; its observed false-promotion count is not itself a statistical bound.

**C.** Null and alternative distributions, dependence, outcomes, and truth are simulated/constructed. A shared-null copied p-value is explicitly marked ineligible; this does not exhaust real shared model/task/scorer dependence. The deterministic online rule is evaluated in registered order; a separate completion order is recorded but does not control decisions. Hard safety remains non-compensable.

**U.** No real GUI, model, task, promotion portfolio, or empirical false-discovery property is measured. Real deployment needs prospective family registration, valid p/e-values, justified dependence assumptions, complete failure retention, and distinct safety gates. This cannot reclassify prior Issues or Results.

## Exact execution record

- Preregistration and source freeze: `PREREGISTRATION.md`, `FREEZE.json`.
- Construction: `python -B -m unittest discover -s scratch/portfolio_multiplicity_5890_t0_v2_20261001 -p 'test_*.py' -v` — 5/5 passed; `python -B -m py_compile ...` — exit 0.
- Start gate immediately before the candidate: main still `3d6ffc76d535309cf3820ed33cb9327354f03648`; all four frozen source hashes matched; raw/audit output paths absent.
- Candidate once: `python -B scratch/portfolio_multiplicity_5890_t0_v2_20261001/runner.py --out scratch/portfolio_multiplicity_5890_t0_v2_20261001/raw-candidate.json` — exit 0, 416 rows.
- Separate raw-only audit once: `python -B scratch/portfolio_multiplicity_5890_t0_v2_20261001/audit.py --raw scratch/portfolio_multiplicity_5890_t0_v2_20261001/raw-candidate.json --out scratch/portfolio_multiplicity_5890_t0_v2_20261001/audit-result.json` — exit 0, `PASS_METHOD_SCOPED`, errors empty, 7/7 corruption controls rejected.
- Candidate raw SHA-256: `f75cce06cc2403346f9918246865f55d529ea9a8cd44c84642ad2b06d6a4482b`.
- Audit result SHA-256: `61edf99f87f928c16621566435958691aa917ad3087affdfad3a173cd7394082`.
- Docker Desktop: configured contexts were observable; the Docker daemon API had failed an earlier short read-only probe. This was a standard-library host-CPU method experiment, not Docker evidence, and no container or shared resource was started or modified.
- Allocation-01's `STOP_MAIN_ADVANCED_AND_STORAGE_ZERO` remains intact. This is a new ID/seed/path/source freeze; no old source branch or result was changed.

