# Issue #5306 — one-step real-options / VOI boundary T1

## Disposition

**PASS_REDUNDANCY_SCOPED.** On the preregistered 405-case finite grid, exact risk-aware one-step VOI and the Bellman STOP/CONTINUE oracle chose identically in all 405 cases. Adding the preregistered separate immediate-downside premium changed 45 stop decisions: 27 selected a continuation whose exact value was strictly below stopping; the remaining 18 were value ties within the preregistered tolerance. The added term created no higher-value choice in this model.

This is a boundary result against one additive-premium operationalization. It does not show that all real-options methods are redundant, or validate the parent #5306 idea.

## H / T / D / C / U

- **H:** If the irreversible-action downside is already included in the decision loss, exact one-step risk-aware VOI may already price preserving the option to delay. Adding a separate expected-downside premium can double count that value and induce dominated waits.
- **T:** Exhaustively evaluated 405 combinations of safe-state prior (5 values), total loss (3), test sensitivity (3), false-pass probability (3), and delay cost (3). Compared immediate expected-utility ADMIT/YIELD, risk-aware one-step VOI, exact one-step Bellman STOP/CONTINUE, and VOI plus a separately added premium.
- **D:** Met: 405 unique rows; independent Decimal audit reports zero errors; VOI/Bellman decisions disagree on 0/405; the separate premium changes 45 decisions, including 27 strictly dominated waits. The other 18 changed choices have equal value within tolerance. Result: PASS_REDUNDANCY_SCOPED.
- **C:** Fully stipulated binary state, known signal model, one optional observation, risk-neutral expected value, additive delay cost, and a calibrated total-loss parameter.
- **U:** No empirical calibration, multi-step information acquisition, dynamic state or deadline, nonstationary/adversarial environment, correlated verifiers, or live interface/action-safety result.

## Provenance

The freeze, formulas, grid, thresholds, and source blob identities are in PLAN.md and the pre-run Issue comment. The runner was executed exactly once in a local CPython 3.11.9 process; the independent Decimal auditor ran once in a separate process. Both exited 0. The audit binds uncompressed stdout SHA-256 `fa237492dd6657da2b98a3b48bc994851e057a70df1c252fbe974a2a5ea22f3a`.

To keep the 198,339-byte raw record without writing to the full C: drive, the repository stores a lossless gzip-compressed, base64-encoded artifact at [results/formal-01/raw.json.gz.b64](results/formal-01/raw.json.gz.b64). Decode it using the instructions in that directory; the decompressed bytes match the auditor's raw SHA-256. The audit JSON is retained beside it.

This was a host-CPU finite boundary run, not a Docker allocation. Docker/OrbStack CLI was not used because current #5085 coordination requires an exact assignment and C: had zero free bytes. No model, GUI, network request, local file write, or external effect occurred. No prior #5306 raw, audit, STOP, or branch was modified.
