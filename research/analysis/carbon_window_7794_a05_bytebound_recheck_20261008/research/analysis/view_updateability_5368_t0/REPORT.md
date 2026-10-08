# T0 result — observation-fiber updateability

Allocation: `view-updateability-5368-t0-hostcpu-20261003-a01`  
Issue: [#6774](https://github.com/Unjuno/agent-interface/issues/6774)  
Parent: [#5368](https://github.com/Unjuno/agent-interface/issues/5368)  
Frozen base: `7446e22459ad79f57828b5699b95ef3c0b504917`

## Disposition

**PASS_METHOD_SCOPED** on the declared nine-case synthetic fixture. Candidate and independent raw-only audit agreed on 9/9 rows; audit status was `PASS_READONLY`, with no errors and no authority/effect emitted.

The fiber-complete gate admitted only the two invariant feasible controls. It requested a disambiguating observation for five mixed fibers (destination, modal, selection, layout generation, and collateral selection), returned `UNTRANSLATABLE` for the impossible requested effect, and `UNKNOWN_MODEL` for the explicit coverage-gap control. Each of the five repair hints matched the first separating field in its frozen ladder.

The freshness-plus-visible-label baseline admitted 9/9 rows and falsely admitted 7 cases under the independent finite oracle: duplicate destinations, hidden modal, hidden selection, stale referent, impossible effect, collateral effect, and out-of-model state. This is a deliberately weak baseline and a finite fixture result, not a prevalence estimate.

## Limits

All outcomes are relative to the enumerated state universe and hand-authored effect oracle. This does not establish GUI state coverage, natural ambiguity frequency, live action safety, model/human behavior, latency, or general view-updateability guarantees. In particular, `UNKNOWN_MODEL` is only an explicit fail-closed control; it cannot prove real-world model completeness.

## Execution and custody

Windows host CPU, Python 3.11.9. Candidate and auditor each ran once from the source frozen in `FREEZE.json`; no retry. No WSLc, container, GPU, network, model, GUI, or input was used. GPU execution was intentionally omitted because this exact finite enumeration is CPU-sized, and #5085 still records unresolved shared-WSLc attribution/no allocation despite a prior infrastructure CUDA smoke and an idle GPU snapshot.

Raw evidence: `candidate.jsonl`, `baseline.jsonl`, `audit.json`; hashes and invocation details: `RUN.json`. Historical #5368 and closed duplicate #6716 are unchanged.

