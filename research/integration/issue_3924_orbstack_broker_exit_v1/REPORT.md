# Issue #3924 — OrbStack broker exit contract v1

**Decision: `PASS_BROKER_EXIT_CONTRACT` (bounded contract only).** The frozen baseline reproduced the zero-to-one exit-code coercion. The isolated one-expression candidate preserved successful zero and propagated a nonzero child status. All seven preregistered cases ran once in the pinned OrbStack container; the independent raw-artifact audit returned zero errors.

| Case | Broker process exit | Observed contract |
|---|---:|---|
| Baseline, fake child exit 0 | 1 | Reproduced suspected defect |
| Candidate, fake child exit 0 | 0 | Zero preserved |
| Candidate, fake child exit 7 | 7 | Nonzero propagated |
| Candidate, fake child timeout | 1 | `HOST_BROKER_SUBPROCESS_TIMEOUT`, no child status |
| Candidate, executable unavailable | 1 | `HOST_BROKER_EXECUTABLE_UNAVAILABLE`, `FileNotFoundError` |
| Candidate, malformed request | 1 | Fail-closed traceback; no receipt/response and no fake invocation |
| Candidate, two requests with `--once` | 0 | Exactly one receipt/response (`r1`); `r2` remains unhandled |

The formal run recorded five fake-executable invocations, zero real model/provider/GUI/task-effect calls, and `authority_granted=false` in broker receipts. Raw requests, responses, receipts, stdout/stderr, process statuses, and the fake argv log are retained under `formal/`. The independent auditor reports `PASS_BROKER_EXIT_CONTRACT`, `errors=[]`.

## Frozen identity and reproduction

- Main source commit: `c83ddb057c680a126144d000bf7ef7ba2274652a`.
- Experiment preregistration commit: `699aae38353cc116973e5ef355571ef341a54df7`.
- Exact runtime source, candidate, fake executable and container image hashes are in `FREEZE.json`; raw artifact hashes are in `formal/SHA256SUMS`.
- Re-run is intentionally not part of verification: the formal matrix was consumed once. Audit existing evidence with the pinned image, network disabled, and read-only source mount.

## Limits / follow-up

This supports a narrow exit-code/receipt contract finding, not a production integration claim. The candidate was not promoted to shared runtime. Malformed JSON fails closed but currently escapes as an uncaught `JSONDecodeError`; a typed malformed-input response is outside this hypothesis and should be a separate successor if prioritized. No model utility, GUI execution, task correctness, provider behavior, or end-to-end broker integration was tested. The prior Linux worker's `STOP_ORBSTACK_RUNTIME_UNAVAILABLE` remains valid for that worker and is not contradicted by this separate Mac OrbStack run.
