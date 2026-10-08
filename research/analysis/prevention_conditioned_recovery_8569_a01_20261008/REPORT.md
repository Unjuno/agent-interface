# Issue #8569 A01 — prevention-conditioned recovery demand

**Disposition: `PASS_METHOD_SCOPED`.** The frozen exact-rational fixture shows the preregistered demand-selection effect and a recovery-strategy ranking reversal. The independent reconstruction matched every output, both controls met their invariants, and all four frozen scoring mutations were rejected. This is a method result over invented values only—not an empirical reliability, recovery-benefit, safety, or product result.

## Result

The initial synthetic regime mix is easy/hard = 4/5 and 1/5. Prevention succeeds with probability 19/20 in easy and 1/5 in hard cases. Consequently, only 1/5 of episodes demand recovery, and that selected population is easy/hard = 1/5 and 4/5.

| Metric | Strategy A | Strategy B | Higher result |
|---|---:|---:|---|
| Unconditional recovery mix | 108/125 (0.864) | 69/100 (0.690) | A |
| Recovery conditional on prevention failure | 129/250 (0.516) | 33/50 (0.660) | B |
| Joint outcome using the selected demand mix | 1129/1250 (0.9032) | 233/250 (0.932) | B |
| Naive joint estimate using unconditional recovery | 608/625 (0.9728) | 469/500 (0.938) | A |

The naive calculation not only overstates the joint outcomes (A by 0.0696; B by 0.006) but preserves the wrong strategy ranking for this fixture. The no-selection control retains the initial mix and identical conditional/unconditional recovery rates. In the equal-sensitivity control, both strategies lose 0.24 when moving to the selected population, so A remains ahead of B.

## Frozen execution and audit

- Freeze commit before the formal run: `865c1cb6f236e4c918b5069bef8219b1139f472b`.
- Construction check, before freeze: `wsl.exe -d Ubuntu -- bash -lc "cd /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_research_8569_prevention_cond_a01_20261008/research/analysis/prevention_conditioned_recovery_8569_a01_20261008 && python3 -B -m unittest -v test_method.py"` — 5 tests passed in 0.002 s.
- Candidate, invoked once at 2026-10-08 08:25:49 UTC: `wsl.exe -d Ubuntu -- bash -lc "cd /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_research_8569_prevention_cond_a01_20261008/research/analysis/prevention_conditioned_recovery_8569_a01_20261008 && python3 -B candidate.py --output candidate_raw.json"` — exit 0; SHA-256 `70aedbeb752235387cd5fcd355e65f72ca6e535398ed223e74e235196a747306`.
- Independent auditor, invoked once after candidate: `wsl.exe -d Ubuntu -- bash -lc "cd /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_research_8569_prevention_cond_a01_20261008/research/analysis/prevention_conditioned_recovery_8569_a01_20261008 && python3 -B auditor.py candidate_raw.json --output audit.json"` — exit 0; exact reconstruction errors: 0; four of four mutation controls rejected; SHA-256 `5c8092c395e28a8cfdcc41f1a1765646e828bf4b124c1a3e5e5f3219a45e299c`.
- Formal candidate/auditor invocation counts: 1/1; retries: 0. No formal output was supplied back to the candidate.
- WSL environment snapshot and the earlier WSLc `E_FAIL` preflight are retained in [`RUNTIME_NOTE.md`](RUNTIME_NOTE.md). The WSLc launcher issue was not treated as a reason to halt; the preregistered native-WSL fallback ran successfully. No container memory enforcement is claimed.

## H / T / D / C / U

- **H:** If prevention disproportionately removes easy cases, the remaining recovery-demand population can be harder and can reverse strategy ranking.
- **T:** One exact-rational candidate over the frozen two-regime fixture; independent oracle; no-selection and equal-sensitivity controls; denominator swap, hard-regime omission, reset-to-initial-mix, and fabricated safe-stop mutations.
- **D:** `PASS_METHOD_SCOPED` for this authored method fixture: the conditional success ranking reverses A→B, the naive joint estimator reverses it back, exact reconstruction has no errors, controls pass, and all mutations are rejected.
- **C:** This selection issue may already be covered by existing intention-to-treat/conditional-fallback metrics; real prevention may be regime-neutral; recovery reset correctness may dominate; and these invented rates may be unrealistic.
- **U:** Two stationary, fully known regimes and invented probabilities. No GUI, live failure, application state, model, user, runtime, or deployed recovery mechanism was exercised.

## Retained artifacts

- [`PREREGISTRATION.md`](PREREGISTRATION.md), [`FREEZE.json`](FREEZE.json), [`trace_fixture.json`](trace_fixture.json)
- [`candidate.py`](candidate.py), [`candidate_raw.json`](candidate_raw.json)
- [`auditor.py`](auditor.py), [`audit.json`](audit.json)
- [`test_method.py`](test_method.py), [`CONSTRUCTION_LOG.md`](CONSTRUCTION_LOG.md), [`RUNTIME_NOTE.md`](RUNTIME_NOTE.md)

Issue #8569 remains an evaluation-method idea; this scoped pass does not close it or establish any product-level reliability claim.
