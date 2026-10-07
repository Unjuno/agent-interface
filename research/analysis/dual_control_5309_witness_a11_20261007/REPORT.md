# Issue #5309 A11 — topology-dependent witness dynamics

## Formal disposition

**`FAIL_AUDIT_MISSPECIFIED_STRATUM_GATE`**. The candidate, environment, and frozen auditor each ran once. The auditor reconstructed all 264 rows exactly, reported zero reconstruction errors and zero authority grants, and found distinct witness-preserving action patterns in all three graph families. The frozen overall gate nevertheless failed because the WITNESS arm completed 3 misspecified cases (GENERIC completed 9), while the preregistration required the WITNESS count to be exactly zero.

This formal disposition is retained. No candidate/environment/auditor reruns or post-outcome source edits were made. The misspecified gate conflates “prediction was wrong” with “the chosen action cannot actually preserve a witness”: the environment derives completion from the actual transition edge. Its exact-row reconstruction found no unsupported completion, but that does not override the preregistered all-zero gate. A11 therefore does not claim a formal PASS or a clean estimate of the broader hypothesis.

## H / T / D / C / U

- **H:** With equal information gain and identical actions, a witness-aware chooser using a correct affordable prediction should outperform lexical choice on witness-backed completion; misspecification should not lead to unsupported completion; over-budget and prior-witness controls should match generic behavior.
- **T:** 132 cases across three directed graph families, all states, correct/inverted predictions, costs 0/1/2, and prior witness absent/present; 264 arm outcomes. CPython 3.14.5, standard-library host processes. Container was unavailable due the existing OrbStack content-store error documented in `PRE_RUN.md`; no container state was pruned or modified.
- **D:** `audit.json` is the formal gate: 264/264 exact reconstruction, zero errors, zero authority, distinct topology signatures, strict correct/affordable increment, zero WITNESS completions under misspecification, and equality on over-budget/prior controls. The final gate returned `FAIL_AUDIT`; thus D is not passed.
- **C:** All graphs and predictions are authored deterministic fixtures. The wrong-prediction rows can still select an edge whose true destination is the witness state; the formal gate did not distinguish that valid realized success from a false completion. No prevalence or calibrated-cost inference.
- **U:** No live GUI/application, model, natural task, latency, calibrated preservation cost, physical input, user, authority, safety, or product-level claim.

## Descriptive outcome

| Stratum | Generic completions | WITNESS completions | Formal gate |
|---|---:|---:|---|
| Prior witness | 66 | 66 | Pass |
| Correct prediction, affordable preservation | 6 | 12 | Strict increment observed |
| Correct prediction, over budget | 3 | 3 | Match observed |
| Misspecified prediction | 9 | 3 | **Fail**: frozen gate required WITNESS = 0 |

The topology construct is effective in this fixture: the actual preserving action varies by state and differs among the three graphs. The A10 historical report remains unchanged; A10's formal auditor failure and topology-invariant mapping are not superseded or rewritten by A11.

## Provenance

See `FREEZE.md` for pre-run source/input hashes, `PRE_RUN.md` for the one-shot commands, `RUN_RECORD.md` for invocation counts and disposition, and `SHA256SUMS.txt` for retained files. The result is method-scoped failure evidence only.
