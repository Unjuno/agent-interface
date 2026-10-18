# A13B preregistration — blinded action-label and readback controls

- Issue: [#5309](https://github.com/Unjuno/agent-interface/issues/5309)
- Allocation: `5309-PRECAPTURE-CONTROL-A13B-20261007`
- Base: `origin/main` `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`
- Node image: `node:26-alpine@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80`

## H/T/D/C/U

- **H:** With the same admissible action set and tied immediate utility/cost/predicted information, witness-aware ranking increases independently receipt-backed completion over lexical task-only plus mandatory postcondition *only* when the lexical action destroys the sole future witness. It adds no completion where a valid independent readback already exists. An allegedly pre-captured but state-perturbing observation cannot count as evidence. An urgent stop and an already-present receipt preempt further action.
- **T:** Six fixed cases, two policies, twelve rows. Two sole-witness cases reverse action labels to test name/order sensitivity; one independent-readback control; one state-perturbing-capture control; one urgent-stop control; one prior-receipt control. Candidate receives only public action descriptors. Environment receives choices and hidden transition/effect truth. Raw-only auditor independently reconstructs each policy choice, action effect, receipt and completion. Three stages run once each in separate containers with stage-specific mounts and no network.
- **D:** PASS requires 12/12 rows, zero reconstruction errors/authority, tied utility/cost/predicted information and identical admissible sets; witness-aware strictly beats task-only in aggregate across the two sole-witness cases despite reversed action-label ordering; both arms tie in the valid-readback control; state-perturbing capture alone never supports completion; urgent stop causes zero actions; prior receipt causes zero new actions and remains independently verified. Any discrepancy is FAIL; pre-formal image/mount/runtime failure is STOP. No retry.
- **C:** All transitions, costs and receipts are authored deterministic fixtures. The action preservation signal is supplied as a public prediction; one toy case family cannot establish calibration or generality. The baseline includes mandatory independent postcondition/readback, not just declared success.
- **U:** No GUI, model, physical input/release, natural task, live authority, calibrated risk/cost, latency, human/product benefit, or safety claim.

## Stage boundaries and one-shot rule

Freeze this protocol, source, public cases, hidden oracle, and image digest before invoking candidate. Candidate stage mounts only `candidate_stage/`; it cannot read the oracle. Environment stage mounts the oracle and candidate choices read-only. Auditor mounts all retained inputs/outputs read-only and writes only its audit output. Do not run candidate, environment, or auditor on the host. After first formal stage invocation, do not edit frozen source or rerun a stage. Construction checks are limited to static case consistency and syntax checks and do not execute the candidate.

## Case definitions

`sole-loss-alpha-first` makes lexical task-only choose the witness-destroying action; `sole-loss-preserve-first` reverses labels so lexical task-only already preserves it. The pair prevents an action-name-only advantage. `independent-readback` provides an independently valid post-action readback even if the volatile receipt is lost. `perturbing-capture` explicitly has no valid independent readback: only a receipt preserved by the selected task action may support completion. `urgent-stop` yields before action. `prior-receipt` verifies an existing receipt and forbids another action.
