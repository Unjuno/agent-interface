# Issue #8668 A05 — emitted-frontier finite protocol

## Question

When the last controller-observed lifecycle phase is `EMITTED`, can a matching cancellation ACK establish that the application effect did not occur? This allocation tests the model boundary between observed dispatch and application consumption. It does not infer that an actual backend emits these ACKs.

## Frozen semantics

- Candidate-visible state is only `observed_phase`, active operation identity, issued requests, received ACKs, neutral-release observation, and whether a retry was requested.
- Evaluator-only `actual_effect_committed` stays in `design.json` and is never copied to candidate input or raw output.
- `CANCEL_ACK` acknowledges the matching cancellation request only. It is not an application no-effect receipt.
- `EFFECT_ACK` confirms application effect only when it matches the issued effect request.
- Before emission (`PROPOSED` or `QUEUED`), a matched `CANCEL_ACK` can classify `CANCELLED_NO_EFFECT` and preserve a requested retry.
- At `EMITTED`, absence of application effect evidence yields `UNKNOWN`; neutral input release has no semantic effect; retries are disabled.
- At `CONSUMED`, a matching `EFFECT_ACK` can classify `EFFECT_CONFIRMED`. Conflicting, unknown, stale, or unbound receipts cannot certify completion or no-effect.

## Policies

`phase_refined` binds receipts to issued request ID, operation ID, attempt and kind, and applies the phase gates above. `phase_blind_request_bound` binds the same identities but ignores the observed phase for a matched cancellation ACK. Both receive identical visible input. The evaluator scores each output against hidden effect truth.

## Run boundary

The allocation is one host-CPU finite schedule run. Candidate and independent auditor each run once after the source freeze; retries are zero. Construction tests before freeze are not allocation invocations. No container, GUI, model, network, OS input, retry, or application effect is used.
