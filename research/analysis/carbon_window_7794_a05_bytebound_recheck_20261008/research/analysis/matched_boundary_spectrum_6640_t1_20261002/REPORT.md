# Issue #6640 — matched-run boundary spectrum T1 result

## Disposition

**`FAIL_METHOD` under the preregistered T1 gate.** The independent raw-only auditor verified the candidate output exactly (`audit_status=PASS`, errors `[]`) but the matched spectrum's improvement over the unstratified baseline was below the frozen minimum. This is a synthetic method result, not a real-trace result or causal diagnosis.

## H / T / D / C / U

- **H:** On this authored finite fixture, within-stratum contrasts should retrieve injected upstream fault boundaries earlier than pooled association and first-symptom order, flag no-overlap/missing exposure, and make no causal claim.
- **T:** 32 seeds × four task/route strata × 64 attempts = 8,192 rows. Candidate saw only observable fixture rows; hidden active-fault truth was mounted only for the separate auditor. WSLc 3.0.1.0, one CPU, exact cached Python digest, no network/pull. Candidate and auditor were each invoked once in separate containers.
- **D:** Frozen pass requires matched mean first-fault MRR to improve by ≥0.10 over every baseline, all-faults top-2 fraction ≥0.75, explicit no-overlap, missingness preservation, complete denominator, and a noncausal interpretation label.
- **Result:** Candidate exit 0 (`CANDIDATE_COMPLETE`), 8,192 rows / 32 seeds. Auditor exit 0 (`audit_status=PASS`, errors `[]`), 8,192 rows / 32 seeds; scientific disposition `FAIL_METHOD`.

| Ranking | Mean first-fault reciprocal rank | All injected faults retrieved by top-2 |
|---|---:|---:|
| Matched-stratum | 1.0000 | 1.0000 |
| Unstratified | 0.9271 | 0.7500 |
| First symptom | 0.2917 | 0.0000 |
| Deterministic random | 0.4042 | 0.2188 |

The matched-vs-unstratified MRR lift is `0.0729`, below the frozen `0.10` requirement. The top-2 gate passes and the first-symptom/random comparisons favor matching, but they do not override the failed all-baselines threshold. Under this fixture, the simpler pooled ranking is already near-perfect, so the predeclared incremental-value hypothesis fails. The output does not say that ranked boundaries are causes.

- **C:** Direct boundary contracts or pooled scores may be sufficient when their ranking is already strong; equal-stratum matching adds no accepted increment under this fixture's threshold.
- **U:** Synthetic authored strata and hidden labels do not estimate natural failure prevalence, causality, real trace quality, inspection utility, or any interface safety/product effect. T0/T2 remain on hold because no retained comparable cohort with independent injected-boundary labels was found. In particular, merged #6523's 12×4 authored event fixture is not such a cohort.

## Integrity and scope

- Candidate raw: 55,668 bytes, SHA-256 `45e6f49834db34b6d015c060077caecb82c2c92108c16f3db1361c2d2abe21c6`.
- Independent audit raw: 499 bytes, SHA-256 `3b9c7265bd149586e83702575b9c5dca3c6d449dfd040df26f9546b8f4d3cd72`.
- Frozen code, protocol and input digests are in `FREEZE.json`; exact commands and stdout/stderr are in `RUN_RECEIPTS.json`.
- Construction: final host 5/5 and final pinned-WSLc 5/5. One earlier WSLc construction command stopped because the cached image lacked pytest; the harness was changed to standard-library unittest before formal start. No package install or network access.
- WSLc warned swap-limit cgroup support was unavailable on both formal invocations. No effective memory-limit enforcement is claimed. There were no running/created containers at preflight; the two new short-lived containers used `--rm`; pre-existing containers were untouched.
- Latest main at start gate: `7f926a27a0ba869dabbf45d6dd21c44bd9665a16`; it advanced after the frozen base `3d768b0b1db255b5dacd099769a30a1b952a3f99`, but the package path was unchanged and CURRENT_GOAL/ROADMAP blob IDs remained identical. Execution stayed bound to the committed freeze; no source was rebased after the gate.
- No model, GPU, CUDA, Docker Desktop, GUI, game, network, task, or user effect was used. Empirical T0/T2 remain `HOLD_NO_COMPARABLE_SPECTRUM`.
- Candidate invocations: 1. Independent auditor invocations: 1. Retries: 0. No raw artifact or earlier STOP was edited.
