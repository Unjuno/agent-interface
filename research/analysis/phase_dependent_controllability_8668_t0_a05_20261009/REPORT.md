# Issue #8668 A05 — emitted-frontier result

**Result: `PASS_METHOD_SCOPED`.** The phase-refined reducer remained `UNKNOWN` and retry-ineligible at `EMITTED` when the matching cancellation ACK acknowledged only the cancel request. This held for two cases with identical candidate-visible input but opposite evaluator-only effect outcomes. The phase-blind request-bound comparator labeled both `CANCELLED_NO_EFFECT` and allowed retry; for the committed-effect case this was one false no-effect claim and one unsafe retry.

The queued pre-emission positive control preserved a valid `CANCELLED_NO_EFFECT` retry. A neutral input release without an ACK after emission did not establish semantic cancellation. A matched effect ACK at `CONSUMED` was recognized, and an ACK with the wrong request ID was ignored. The independent auditor reconstructed all 6 cases, reported zero phase-refined false no-effect claims and zero unsafe retries, and rejected all 3 corruption controls.

Candidate-visible input and raw output contain no `actual_effect_committed` field. The auditor alone joins the hidden truth from the frozen design; the two emitted cases have byte-identical visible views and different truth values.

## Execution and provenance

The source freeze is commit `c16c8a57a5e2a2598b3bae94f50d65f631f2dedf`, based on exact current main `a6343bb76e4dc0a4afa32a29c8a485a617faeff8`. Candidate and auditor each ran once with network denied, both exit code 0, no retries, and empty stderr. The candidate and audit output hashes are in `RUN_RECORD.json`; all retained files are covered by `SHA256SUMS.txt`.

Construction tests passed 4/4 on Python 3.12 and 3.14, normally and under `-O`. The allocation itself used CPython 3.14.5 on macOS 27.0.1 arm64, host-only. No container, GUI, model, OS input, cancellation, retry, or application effect was dispatched.

## Scope

This confirms only the preregistered finite transition contract. It does not establish that a real backend exposes trustworthy `EMITTED` phases, that `CANCEL_ACK` has these semantics, that a GUI effect was prevented, or that the reducer improves task success or latency. If a backend provides an independently authoritative application no-effect receipt after emission, that receipt needs a separately frozen study.
