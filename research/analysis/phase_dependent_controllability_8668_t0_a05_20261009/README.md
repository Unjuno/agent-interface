# Issue #8668 A05 — emitted frontier with hidden application effect

This finite model isolates one phase omitted from A04's retained schedule coverage: the controller has observed `EMITTED`, but has not observed whether the application consumed the operation. Two frozen cases have identical controller-visible input and different evaluator-only effect outcomes. The candidate never receives the hidden outcome.

The result concerns only the authored transition contract. It does not dispatch a GUI action, OS input, cancellation, retry, or application effect.

## H/T/D/C/U

- **H:** A request-bound but phase-blind reducer can classify an ACK as cancellation success after observed emission even when the application effect may already have committed. A phase-refined reducer should report `UNKNOWN` and disallow retry until application effect state is resolved.
- **T:** Evaluate six frozen schedules: a valid pre-emission cancellation; a matched ACK at `EMITTED` with the same visible input but opposite hidden effect outcomes; neutral release without ACK after emission; a consumed effect ACK; and a stale request ACK. Compare phase-refined and phase-blind request-bound policies, then independently reconstruct raw output and run three corruption controls.
- **D:** `PASS_METHOD_SCOPED` only if all six rows match the auditor, phase-refined output has zero false no-effect claims and zero retries after an actually committed effect, the two identical `EMITTED` views both remain `UNKNOWN` with retry disabled, the queued positive control preserves retry eligibility, the phase-blind policy yields the preregistered false-cancel/unsafe-retry witness, and all three mutations are rejected. Otherwise report `FAIL_METHOD` or `HOLD_METHOD`.
- **C:** The backend may expose an authoritative no-effect receipt after emission; this model does not define such a receipt. A real backend may also lack reliable phase or effect acknowledgements, in which case `UNKNOWN` is the only supportable state.
- **U:** Finite authored schedules do not establish real dispatch phases, receipt semantics, GUI behavior, task outcomes, or retry safety. `actual_effect_committed` is evaluator-only truth, not candidate input.
