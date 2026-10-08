# Issue #5309 A13B — pre-capture/readback controls

## Verdict

`PASS_PRECAPTURE_CONTROL_SCOPED` on the frozen finite fixture. The result supports only a narrow method distinction: a witness-preservation ranker can prevent loss of the sole independent post-action receipt in this authored model; when an independent readback exists, it adds no completion in the control. It is not a GUI or product result.

## H/T/D/C/U

- **H:** With equal admissibility and tied immediate utility/cost/predicted information, witness-aware ranking increases independently receipt-backed completion over lexical task-only only when the latter destroys the sole future witness. It adds no completion where independent readback exists. State-perturbing capture is not evidence. Urgent stop and an existing receipt preempt further action.
- **T:** Six cases, two policies, 12 rows. Candidate, effect environment, and raw-only auditor each ran once in separate pinned Node 26.10.0 Alpine containers with no network, read-only root, bounded resources, dropped capabilities, and stage-specific mounts. Candidate had only public action cases; oracle/effect truth was mounted only in environment and auditor stages.
- **D:** All 12 rows independently reconstructed; errors 0; authority grants 0; identical admissible action sets and tied utility/cost/predicted information; strict witness-aware advantage in the two label-reversed sole-witness cases; tie in independent-readback control; no evidence credit from perturbing capture; urgent-stop arms took no action; prior-receipt arms took no new action.
- **C:** Authored deterministic transitions and public witness-route predictions can favor this policy. The sample is intentionally tiny; no probability/cost calibration, uncertainty interval, or generalization follows.
- **U:** No GUI, model, physical input/release, natural task, live authority, calibrated risk/cost, latency, reliability, user/product benefit, or safety claim.

## Results

| Stratum | TASK_ONLY independently verified | WITNESS_AWARE independently verified | Interpretation |
|---|---:|---:|---|
| Sole witness, lexical loss first | 0/1 | 1/1 | Witness-aware preserved the only receipt. |
| Sole witness, preserving action first | 1/1 | 1/1 | Reversing action labels removes the apparent name-order advantage. |
| Independent readback | 1/1 | 1/1 | Both choose lexical action; no incremental completion. |
| Perturbing capture | 0/1 | 1/1 | Capture itself is invalid; only the preserved post-action receipt supports the latter completion. |
| Urgent stop | 0/1 actions | 0/1 actions | Both yielded before any task action. |
| Prior receipt | 1/1, no new action | 1/1, no new action | Existing receipt preempted further action. |

Across the two preregistered sole-witness cases, task-only completed 1/2 and witness-aware 2/2. The auditor ignored candidate completion hints: 10 hints were emitted across action/prior-receipt rows, while only 8 rows had oracle-supported effect/receipt evidence. The two unsupported hints remained non-authoritative and were not counted as completions.

The `PERTURBS_STATE` row did not use capture as a witness: its `independent_readback` oracle bit is false, and auditor completion derives only from an actual effect plus a surviving receipt (or, in the separate readback control, an independent readback).

The control encodes independent-readback availability as a frozen oracle condition; it does not execute or model a pre-action capture operation. Thus the equal-performance control shows only that the witness-preservation policy adds nothing when an independent readback is stipulated to exist. It does not show that a safe pre-action capture can reliably create such a path, nor does the perturbation flag calibrate real observer backaction.

## Reproduction and provenance

- Frozen main: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`.
- Freeze commit: `9f3ab7bb92ddc026330677a1cb71844883c62c5b`.
- Allocation: `5309-PRECAPTURE-CONTROL-A13B-20261007`.
- Construction: `node construction_test.mjs` passed before freeze.
- Source/input hashes: `FREEZE_SHA256SUMS.txt`; formal output hashes and exact one-shot command outcomes: `FINAL_SHA256SUMS.txt` and `RUN_RECORD.md`.
- A13's pre-freeze STOP remains a separate immutable allocation ([PR #8299](https://github.com/Unjuno/agent-interface/pull/8299)); A13B is a fresh, independently frozen successor, not a relabeling or rerun of A13.
