# A01 result — `PASS_COUNTEREXAMPLE_ONLY`

This is one exact shared-source non-identifiability control within #8887's proposed factorial T0. It is **not** the full T0, not a validation of a latent-class estimator, and not a real-checker result.

## H / T / D / C / U

- **H tested:** If several checker columns are all driven by one shared bit, identical no-gold observations can be compatible with materially different checker correctness. Agreement alone must not be promoted to accuracy without an additional, justified independence/lineage assumption.
- **T executed:** The frozen candidate emitted eight observed rows for four identical checker columns (`00001111`) and reported no-gold accuracy as unidentifiable. A separately written auditor compared two hidden truth assignments without exposing them to the candidate, verified all row-level and summary values, and ran four frozen mutation controls.
- **D:** `PASS_COUNTEREXAMPLE_ONLY`. The observations, checker marginals, and all pairwise agreement statistics are identical in both worlds; truth prevalence is 0.5 in both; finite-panel checker correctness is 1.0 in world A versus 0.5 in world B; candidate abstains from an accuracy estimate; the independent auditor exits 0 and rejects all four mutations.
- **C:** A separately established source-distinctness/conditional-independence contract or an independent gold subset could narrow the admissible worlds and permit a scoped reliability estimate. This control does not test such a method.
- **U:** Eight constructed rows only. No sampling uncertainty, prevalence grid, Dawid–Skene/Hui–Walter fit, conditional-dependence model, cross-stratum drift, selective missingness, real GUI, or real checker was tested. `PASS_METHOD_SCOPED` for #8887 is not claimed.

## Exact execution record

- Base main: `964c9197d5083ab55ea7fdc9105427623e89e677`
- Frozen source commit: `2cb3f7bff7cfadcec0976409c39fdf182ee53604`
- Allocation: `8887-common-mode-observational-equivalence-a01-20261012-01`
- Runtime: local Windows CPython 3.12.10; Python standard library only. No WSL/WSLc/Docker, package installation, GUI, model, network, human, or external effect.
- Candidate command: `python research/analysis/no_gold_effect_identifiability_8887_a01/candidate.py research/analysis/no_gold_effect_identifiability_8887_a01/result.json` — invoked once, exit 0, stdout `candidate_written`.
- Auditor command: `python research/analysis/no_gold_effect_identifiability_8887_a01/audit.py research/analysis/no_gold_effect_identifiability_8887_a01/result.json research/analysis/no_gold_effect_identifiability_8887_a01/audit.json` — invoked once, exit 0, stdout `PASS_COUNTEREXAMPLE_ONLY`.
- Retries: 0. No code changes after the source freeze.
- Pre-freeze source syntax: `AST_PARSE_PASS`; source freeze `git diff --check`: pass. Post-run `git diff --check`: pass.

The two worlds have the same shared observations `00001111` for all four checkers and the same 50% truth-label prevalence:

| Hidden world (auditor only) | Truth labels | Each checker's finite-panel correctness |
|---|---|---:|
| A — shared bit equals truth | `00001111` | 8/8 (1.0) |
| B — common-mode output with different truth | `00110011` | 4/8 (0.5) |

All six checker-pair agreement values are 1.0 in both worlds. The candidate record contains no truth labels and returns `UNIDENTIFIABLE_WITHOUT_INDEPENDENCE_EVIDENCE`, with `accuracy_estimate: null` and `confidence_claim: null`. The auditor rejected checker-bit flip, dropped-row, duplicate-row-ID, and unsupported-accuracy-claim mutations.

## SHA-256

- `README.md`: `73f4225bc213dc54d4914aa384e5a1002e48efd0e93aed34def8648568e627d0`
- `candidate.py`: `f46e57164b73b7929e102f09da799d5663ee672257b9c8c71fe7937a50d1250e`
- `audit.py`: `da24ccebc9f8e833f367a3dc0ee733ad5c6bfc8d5d144ef9ab7dfffbddd0343e`
- `result.json`: `bc20b42b465bd94fdd47e395f837656bb24d5615eaf25ac005efeb39b04612b1`
- `audit.json`: `f37e282e67c8b7263ee9a5e7e36cc623a1922c2e49d205d2aad8b42714e68565`

## Interpretation and next discriminator

The control shows that agreement is an observable property of the checker panel, while accuracy depends on the latent truth relation. A method receiving only this matrix cannot distinguish these worlds. A broader #8887 study should now test which external assumptions or observable source-lineage diagnostics can safely exclude the common-mode world, and when the method must keep returning `UNIDENTIFIABLE`. It should not infer that all no-gold estimation is impossible under every defensible assumption.
