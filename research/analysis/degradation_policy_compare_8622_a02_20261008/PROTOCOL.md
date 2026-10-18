# A02 protocol — Issue #8622 successor to #8610

## H/T/D/C/U

- **H:** Under common-cause failures, an independence-assuming component lookup admits unsupported operations; a dependency-aware contract blocks them while preserving an independently supported limited outcome; unknown-dependency fail-closed admits no operation.
- **T:** Evaluate the exact ten-case fixture in spec.json with three policies: independence_assuming_lookup, dependency_aware_contract, and unknown_dependency_fail_closed. An independent auditor recomputes all arm outputs from the graph and evidence. Six semantic corruption controls exercise operation omission/addition, claim promotion, unauthorized dispatch, lost release obligation, and graph mutation.
- **D:** PASS_METHOD_SCOPED only if the naive arm exposes all planted common-cause overclaims, the dependency-aware arm exactly matches independently reconstructed support, the unknown fail-closed arm admits zero operations in the unknown case, the auditor reconstructs 10/10 cases, release obligations are preserved 10/10, no dispatch occurs, and all six mutations fail audit. Any missing/wrong arm invalidates the issue-level gate.
- **C:** A sufficiently conservative independence lookup may match the dependency-aware contract; no selective value is then demonstrated. If the graph has no defensible independent channel, selective preservation is not identified.
- **U:** Hand-authored finite graph only; no production topology or reliability-rate inference. No GUI, runtime, human benefit, latency, safety, resource-enforcement, or product claim.

## Run constraints

Freeze all test/source/input bytes before formal invocation. Candidate and auditor each run once, no retries. Host-only CPU execution with stdout/stdin in memory is selected because C: has no free space and #7924 holds the shared WSLc lane. The candidate and auditor do not perform task actions or external effects. Preserve all setup failures and exact stdout hashes.
