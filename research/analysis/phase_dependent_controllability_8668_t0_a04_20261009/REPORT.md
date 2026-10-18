# Issue #8668 A04 — request-bound ACK transition result

**Result: `PASS_METHOD_SCOPED`; subhypothesis: `SUPPORT_FOR_REQUEST_BOUND_ACK_TRANSITIONS_SCOPED`.** The candidate and independent raw-only auditor each ran once under network denial (exit 0, retries 0). The auditor reconstructed all 18 frozen schedules, reported zero errors, and rejected all 8 mutations.

On these authored schedules, binding an ACK to the issued request ID, operation ID, and attempt made the expected distinction from the latest-ACK-type-only comparator in 12/18 rows. Five preregistered stale/unbound witnesses passed: prior operation, prior attempt with a reused operation ID, mismatched request ID, absent request, and late cancellation after effect. The request-bound reducer preserved four eligible pre-emission cancel/no-effect retries. From the retained raw, the latest-type-only comparator produced 3 false completion classifications and 6 unsafe retry classifications; request-bound output had zero false completions, false cancellations, unsafe retries, neutral-release aborts, accepted stale/unbound receipts, or conflicting-ACK success.

## Method and environment

The frozen design supplies each policy the same operation phase, actual effect state, issued-request ledger, ordered receipts, neutral-release observation, and retry request. The candidate emits advisory classifications only; it dispatches no cancellation or retry. OrbStack's read-only image inventory failed before listing an image because containerd could not read blob `sha256:253e23fe66fc4ea0cdbfd1124a9495fc8b0c8a4acc9a523cd35a9808ed63f67a` (`operation not supported`). The method therefore ran host-only under macOS `sandbox-exec` network denial using CPython 3.14.5 and the standard library. No container is claimed.

Pre-freeze construction tests passed 4/4 normally and 4/4 under `-O`. Exact source, environment, and commands are recorded in `FREEZE.json`, `ENVIRONMENT.json`, and `RUN_RECORD.json`; the package manifest covers every retained file.

## Scope boundary

This supports only the authored finite request/receipt-binding subhypothesis. It does not resolve the broader #8668 stale-ACK transition HOLD, establish that a real backend emits these identities or receipts, test GUI cancellation or input release, authorize retry, or show task/product effectiveness. A03's narrower result and all earlier A01/A02 records remain unchanged. No runtime code changed.
