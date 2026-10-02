# Issue #6422 T0 result — denial-aware approval requests

## Result

**`PASS_METHOD_SCOPED` for the finite synthetic policy fixture only.** The candidate compared 14 frozen histories under ID-only retry, a one-follow-up count cap, and an effect-aware denial ledger. The independent raw-only auditor reconstructed all 14 cases with no errors.

| Policy | Equivalent denied-effect re-asks | Legitimate fresh requests blocked | Safety release |
|---|---:|---:|---|
| ID-only | 6/7 allowed by the control | 0/4 | allowed |
| One-follow-up cap | 0/7 | 4/4 | allowed |
| Denial ledger | 0/7 | 0/4 | allowed |

The denial ledger blocked same-effect retries across new IDs, paraphrase, route change, narrowed-looking text, an alternate non-veto principal, elapsed time and same-ID retry. It allowed a fresh confirmation request for a materially changed recipient, authenticated user reopening, no-response, and a source-stated deferral with matching independently verified evidence. The last case was only eligible to ask again; it did not authorize sending. Ambiguous effect equivalence and agent-asserted condition satisfaction held. Emergency cancel/release remained allowed.

The independent auditor rejected all four frozen corruptions: erased denial, forged reopening, changed required-principal mapping, and hidden effect component. Exact output and audit report hashes are in `RUN.json` and `SHA256SUMS.txt`.

## Method and environment

- Formal candidate: one invocation, exit 0; formal independent auditor: one invocation, exit 0; formal retries: 0.
- Construction suite: 6/6 passed on CPython 3.11.9. Test-first red failures due to missing entrypoints and the two construction candidate invocations are itemized in `BUILD_HISTORY.md`; they are not hidden or counted as formal retries.
- Executed locally on Windows host CPU. Shared WSLc had three unrelated exited containers in the read-only inventory, so this run did not create or touch containers. No Docker, WSL, model, GPU or CUDA was invoked; this synthetic contract test does not need them. Therefore this is host-only evidence, not a container-portability result.
- Frozen package source was read back from its additive GitHub branch and text-compared byte-for-byte before the formal invocation. Source/input SHA-256 values are in `FREEZE.json`.

## Scope and next boundary

This does not evaluate model-generated requests, user pressure/coercion, human behavior, real approval flows, authority correctness, GUI state, or prevention of an actual effect. It does not establish an H result or justify a T1 model run. Issue #6422 remains open for separate review and any later T1 still requires its own budget and no-effect protocol. No GPU conclusion is implied.
