# V39 typed-health event availability timing A01 — preregistration

Status: FROZEN BEFORE CANDIDATE RUN
Parent: v39 typed-health short-window coalescing A02
Issue: #59
Immutable trace base: main `2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0`
Inputs: report blob `bff2459036dcdcc44ed100b0c0bc657e1bb8e69a`; event stream blob `cbaeed9c7ba27b53cef9d10730ae33313371ad9a`.

## H/T/D/C/U

- **H:** The capture-time replay of the two-downward-transition rule may overstate or understate when its signal is actually available to a monitor. Replaying the exact same rule on emitted-time should reveal sequence changes or a measurable availability delay.
- **T:** Run the same six waits and the frozen W grid {0.5, 1, 1.5, 2, 2.5, 3, 4}s twice in memory: (a) timestamp samples by the health signal's capture_ns; (b) timestamp them by the enclosing typed_observation event's emit_ns. Compare trigger/no-trigger, selected sequence, and trigger offset from controller-model start; report capture→emit delay for selected samples. This is a timing-source comparison, not another hypothesis-threshold search.
- **D:** Same immutable report/event blobs as A02, 634 JSONL records / 218 typed observations / six waits. No new runtime or external state.
- **C:** Keep the health transition rule and all windows unchanged. For each clock, sort observations on that timestamp, select the last valid sample at/before model start, and count an adjacent observed numeric decrease whose second sample lies within the model wait. Unknown samples clear the chain. The second decrease is the trigger. Report the full 6×7 table for both clocks; do not select a preferred clock from outcome.
- **U:** Single saved stochastic trace. Timestamp availability is only one component of interruption latency; this does not establish observer transport, actual interrupt send/ack, effect, safety, or benefit.

## Gates

- **PASS_SCOPED:** exact input identities/counts, all 84 clock×wait×decision entries, and an independent alternate implementation agree.
- **FAIL:** the candidate rule cannot be replayed under the frozen clock definition; retain output.
- **HOLD:** missing or inconsistent timestamps.
- **STOP:** any live runtime/model/game/input is started or any intervention authority is inferred.

No thresholds, sources, or live allocation are changed.
