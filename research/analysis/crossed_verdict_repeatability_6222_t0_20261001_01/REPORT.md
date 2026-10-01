# Issue #6222: crossed verdict repeatability T0

**Disposition: `PASS_METHOD_SCOPED`.** This finite synthetic assay detected the preplanted ranking fragility without disturbing the stable control, while keeping shared bias, semantic UNKNOWN, and missing evidence distinct. It does not validate any live benchmark, production scorer, model, or route comparison.

## Frozen execution

Allocation `CROSS-VERDICT-REPEATABILITY-6222-T0-HOST-20261002-01`; owner Unjuno / local Codex task `01a0b990-3d17-72f1-a908-9a2072104ce5`; source main `673763554192ae26636e07d5a48f03b3cd7fb044`; branch `research/6222-crossed-verdict-repeatability-t0-20261002-a02`. The one-shot CPU-only host window was 2026-10-01 20:05–20:25 UTC. No model/application, network, CUDA, GPU, Docker, or WSL was used. Candidate ran once (exit 0); the separate raw auditor ran once afterward (exit 0). No retry or alternate seed.

The immutable freeze, H/T/D/C/U preregistration, runner, construction log and six source artifacts are retained alongside this report. The formal runner's output-collision and source-hash checks passed. Construction test passed 1/1. Preparation failures and correction are preserved in `CONSTRUCTION_LOG.md`; they were not formal runs.

## Observations

The fixture crossed 24 synthetic artifacts over two evaluators, two setups and three repeats (288 observations), plus 24 fixed-reference observations.

| Case | One-pass | Crossed admissible rankings | Result |
|---|---|---|---|
| Stable control | A>B | A>B | Preserved |
| Within-scorer planted flip | A>B | A>B, B>A | Fragility exposed; 2 flip cells |
| Setup-dependent planted flip | A>B | A>B, B>A | Fragility exposed; 14 setup-disagreement cells |
| Shared-bias consensus | TIE | TIE | B2 flagged; consensus explicitly not a validity certificate |
| Semantic ambiguity | TIE | TIE | 12 UNKNOWN observations retained |
| Differential missingness | TIE | TIE, UNRESOLVED | 3 missing rows retained; B's interval widened to [0.5, 1.0] |

The fixed positive/negative reference deck passed. The independent auditor reconstructed all 288 candidate rows and the summaries with zero errors, bound the expected and observed allocation IDs and main SHA, and rejected all five preregistered mutations: allocation-ID substitution, row omission, verdict flip, oracle tampering, and missingness laundering. Candidate SHA256: `ce85e4970fdc9467acc918f10b3c23f8b175283878fa2d505eeadaa6af839696`; audit SHA256: `ecfe2e5bb9e21e396ea564a44cafcc8ce5feac4310253d6fa2a6710c6dfcc7d9`.

## Interpretation and limits

This supports the narrow method claim that a fixed standards deck can pass while crossed repeated scoring reveals deliberately planted ranking reversals. It is a designed positive-control demonstration, not an estimate of real evaluator instability, prevalence, or operational value. A real successor needs immutable eligible artifacts and genuinely independent scorer/setup paths; absent those, report HOLD rather than manufacture repetitions or call consensus truth. UNKNOWN is semantic ambiguity, not scorer error. Missingness is bounded, not silently dropped. No existing benchmark scores or earlier results were modified.

## Reproduction and retained evidence

Read `FREEZE.json` and `PREREGISTRATION.md` first. Raw outputs: [`candidate.json`](formal-output-01/candidate.json), [`audit.json`](formal-output-01/audit.json), [`RUN.json`](formal-output-01/RUN.json), and [`SHA256SUMS`](formal-output-01/SHA256SUMS), with candidate/auditor stdout and stderr in the same directory. The formal run is one-shot; do not rerun into this occupied output path.

