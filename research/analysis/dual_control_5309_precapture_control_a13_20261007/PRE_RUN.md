# A13 preregistration — pre-capture and witness-preservation controls

> PLAN ONLY. This document was not committed or checksum-frozen before the candidate invocation. The authoritative disposition is [STOP.md](STOP.md); this plan is retained to show the intended question and gates, not as a valid preregistration.

- Issue: [#5309](https://github.com/Unjuno/agent-interface/issues/5309)
- Allocation: `5309-PRECAPTURE-CONTROL-A13-20261007`
- Base checkout: `origin/main` at `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`
- Verdict vocabulary: `PASS_PRECAPTURE_CONTROL_SCOPED`, `FAIL_*`, `STOP_*`.

## H/T/D/C/U

- **H:** A witness-preservation constraint improves independently verified task completion only when the action would otherwise destroy the only source-bound effect witness. It should provide no incremental benefit when a valid independent baseline/readback path already exists, should reject a purported pre-capture that perturbs the state, and should yield before information gathering on urgent stop.
- **T:** Exhaustively run a deterministic finite paired-action fixture. The task-only comparator and witness-aware policy receive identical admissible actions, utility, cost, predicted information gain, and safety envelope. Controls vary (1) witness-destroying versus preserving transition, (2) independent pre-action baseline/readback availability, (3) state-perturbing capture, (4) an already-present receipt, and (5) urgent stop. Candidate, environment, and raw-only auditor run in separate digest-pinned, network-disabled containers. Candidate receives no oracle/transition truth.
- **D:** PASS requires exact reconstruction of every frozen case; equal admissibility/utility/cost/predicted-information inputs across actions; strictly more independently receipt-backed completions for witness-aware than task-only in the sole-witness-loss stratum; no incremental advantage where an independent baseline/readback is available; no completion credited to a perturbing capture; zero actions under urgent stop or prior receipt; and zero authority grants. Any mismatch is retained as FAIL; container/source/mount failure before formal invocation is STOP.
- **C:** Authored deterministic transitions and evidence channels are intentionally small and can encode the desired distinction. The result is a method counterexample/control, not a calibrated policy comparison. A real effect protocol may make pre-capture/readback unavailable or costly.
- **U:** No GUI, model, physical input/release, natural task, live authority, calibrated risk/cost, latency, reliability, user/product benefit, or safety claim.

## Freeze and one-shot execution rules

Source, cases, expected gate, image identity, and container command are frozen before formal stages. Run candidate, effect environment, and auditor exactly once each. No retries or source edits after the first formal launch. Preserve stdout/stderr/exit status and hashes. Construction tests are not formal results. The candidate mount must exclude `oracle.json`; the environment receives choices plus oracle; the auditor receives all outputs read-only. Formal result is published to #5309 and a PR only after all retained checks.

## Frozen case semantics

Each action achieves the same task effect and has the same utility/cost/predicted information gain. In `SOLE_WITNESS`, lexical task-only selection destroys the only post-action independent witness while the other action preserves it. In `INDEPENDENT_READBACK`, either action remains independently verifiable, so witness-aware ranking must not claim an incremental completion benefit. `PERTURBING_CAPTURE` marks pre-capture evidence invalid for effect verification. `PRIOR_RECEIPT` and `URGENT_STOP` require no action. The oracle, not candidate hints, determines the realized task effect and receipt-backed completion.
