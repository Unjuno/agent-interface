# Issue #8185 A01 post-run qualification

**Disposition: the retained A01 `PASS_METHOD_SCOPED` does not establish Issue #8185's preregistered discriminator.** The original protocol, candidate, oracle file, outputs, run receipt, and their `SHA256SUMS` remain unchanged. This is a read-only post-run source/output assessment; candidate, auditor, construction suite, and formal allocation were not rerun.

## Directly verified method gaps

- In `epoch_transform_chain_8185_t0_20261005/audit.py`, `baseline()` returns `UNKNOWN_REFUSE` whenever `len(edges) != 1` (line 26). It therefore refuses every composed path rather than applying the specified capture-origin plus last-known scale/offset comparator with a declared calibration-update schedule. It also refuses residual/correlated uncertainty (lines 30–31), so its five valid-stratum refusals cannot be interpreted as a fair estimate of the target baseline's false-UNKNOWN rate.
- The A02 issue description says five of eight valid rows are multi-edge. Directly counting the frozen A01 `candidate_input.json` against `oracle_truth.json` shows three: `mixed_monitor_update`, `two_epoch_composition`, and `composed_small_uncertainty`. The other two baseline refusals are `shared_uncertainty_control` and `independent_error_crosses_edge`, rejected by the baseline's uncertainty guard. This corrects the issue description's attribution without changing either allocation.
- `two_epoch_composition` contains three edges, but all three have epoch 1; it does not exercise a 7→8→9 validity transition.
- `oracle_truth.json` contains expected mapped points and target geometry/identity, but no hidden edge matrices. `independent_oracle()` in `audit.py` reads the authored `expected_point`; the auditor checks candidate coordinates against that point rather than independently composing exact hidden transforms. Thus zero mismatches in the saved audit does not prove the required independent exact-transform-oracle gate.
- A01 ran host-only after OrbStack image inventory failed. The subsequent Issue #8201 protocol explicitly disallows that fallback for A02; A01's host result remains preserved but is not compliant evidence for that container-gated allocation.

## Consequence

The 80% false-UNKNOWN reduction is a description of this authored fixture and comparator implementation only. Because comparator calibration/fairness, epoch composition, and independent exact-oracle requirements were not met, do not treat A01 as a PASS of Issue #8185's hypothesis or merge PR #8199 as the issue's completed experiment. A02 remains separate and currently has a pre-candidate OrbStack STOP; no formal candidate result exists.

## Evidence pointers

- Frozen A01 protocol/report/run/source/output: `epoch_transform_chain_8185_t0_20261005/`.
- A02 runtime STOP and post-STOP observations: `epoch_transform_chain_8185_a02_20261005/`.
- Independent package integrity: A01's original `SHA256SUMS`; this qualification's separate `POST_RUN_QUALIFICATION_SHA256SUMS`.
