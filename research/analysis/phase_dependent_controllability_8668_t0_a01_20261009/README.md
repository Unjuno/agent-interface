# Issue #8668 T0 — phase-dependent controllability under bounded delay

## H / T / D / C / U

**H.** In the declared finite plant, an event-wide `CANCELABLE` label will falsely report cancellation in at least one schedule where the operation has crossed the `EMITTED` frontier; an event-wide `UNCONTROLLABLE` label will miss at least one safe pre-emission cancellation. A phase-refined policy will preserve every modeled pre-emission cancellation with a matching removal confirmation, keep late or unconfirmed operations `UNKNOWN`, and never admit a duplicate retry while the original effect is unresolved.

**T.** Enumerate one no-input control plus the full Cartesian product of five cancellation request phases (`PROPOSED`, `ADMITTED`, `QUEUED`, `EMITTED`, `CONSUMED`), control-delivery delay 0/1 transitions, cancellation-reply delay 0/1 transitions, boundary tie order (`CONTROL_FIRST`, `PLANT_FIRST`), effect-receipt observation delay 0/1 decision boundaries (`EFFECT_FIRST`, `RELEASE_FIRST`), stale receipt position (`NONE`, `BEFORE_RETRY`, `AFTER_RETRY`), and retry requested/not requested. `EFFECT_FIRST` means the effect receipt is observed before the retry decision; `RELEASE_FIRST` means the neutral-input receipt arrives first and the effect receipt arrives one decision boundary later. There are 480 requested-operation schedules plus one no-input control. The event trace separates command delivery, proven pre-emission removal, effect commit/receipt, physical input release/receipt, timeout, retry, and a stale receipt from a different operation ID.

The candidate and raw-only auditor are separately implemented in the standard library. The auditor reconstructs every case and policy result without importing candidate code and runs five corruption controls: phase relabel, delay-bound change, dropped pending case, stale operation-ID acceptance, and treating input release as semantic abort.

**D.** `PASS_METHOD_SCOPED` requires exactly 481 unique schedules, exact candidate/oracle reconstruction, at least one false cancellation by the static-cancelable policy, at least one missed safe cancellation by the static-uncontrollable policy, zero false cancellation claims and zero unsafe duplicate admissions by the phase-refined policy, preservation of all cancellation opportunities the frozen model makes safe, and rejection of all five mutations. Any oracle disagreement, missing case, unsafe duplicate, false cancellation, or accepted mutation is `FAIL_METHOD`; inability to establish the declared finite state is `HOLD_MODEL_UNIDENTIFIABLE`.

**C.** Operation-bound terminal accounting plus `UNKNOWN` (as studied in #6664) may be sufficient without a phase-refined controller; a static label may also be adequate for a different plant whose cancellation frontier does not move. The modeled contrast depends on the declared rule that emission is the irreversible frontier.

**U.** This is a synthetic deterministic transition model, not a runtime defect reproduction. The bounds, event order, removal acknowledgement, and frontier are authored. It does not establish that any OS/backend exposes these phases or acknowledgements, or measure GUI success, input neutrality, latency, model use, or product safety. No runtime, GUI, model endpoint, Docker/OrbStack daemon, or network call is part of T0.

## Frozen plant and policies

The operation has a non-idempotent effect and phases `PROPOSED → ADMITTED → QUEUED → EMITTED → CONSUMED → EFFECT_CONFIRMED`. A cancellation request is distinct from its delivery acknowledgement. Only an operation-bound removal confirmation that wins before `EMITTED` proves cancellation. At the `EMITTED` boundary, `CONTROL_FIRST` means the acknowledgement wins the tie and `PLANT_FIRST` means emission wins. A late command-delivery receipt is not proof of removal. After emission, the effect eventually commits in this finite plant; its observation may arrive before or one decision boundary after the input-release receipt. Releasing held input establishes only physical neutrality. A receipt carrying a different operation ID is stale. Timeout does not cancel an operation.

Policies compared: (1) static-cancelable, which treats a delivered cancel command as semantic cancellation at any phase; (2) static-uncontrollable, which refuses cancellation at every phase; (3) fail-closed, which blocks retries while the operation has no terminal evidence; and (4) phase-refined, which requires exact operation identity and pre-emission removal proof and otherwise retains `UNKNOWN` until effect confirmation. These are synthetic comparators, not source claims about existing runtime policies.

## Execution record

- Issue: [#8668](https://github.com/Unjuno/agent-interface/issues/8668)
- Allocation: `PHASE-CONTROL-DELAY-8668-T0-A01-20261009` (deterministic construction/model-check rung only)
- Frozen main: `23d1807ffad8359e0f89421ee2b9bf5783c9d5f4`
- Branch: `research/8668-phase-control-delays-a01-20261009`
- Output: `run-01/` (must not exist before the frozen candidate invocation)
- Runtime: host-local Python standard library; no container or shared service required by this finite model.
- Frozen hashes and exact invocation are in `FREEZE.json`; the first output and raw-only audit are retained under `run-01/`.
