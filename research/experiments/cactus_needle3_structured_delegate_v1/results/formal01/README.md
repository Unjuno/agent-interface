# Formal allocation 01 — unchanged one-shot result

**Decision: `FAIL_CACTUS_NEEDLE3_YIELD_BOUNDARY`.** This is one formal invocation of allocation `cactus-needle3-base-structured-action-20260926-01`; no retry, prompt edit, model replacement, tuning, or GPU path was used. The local raw result is preserved verbatim in `formal-result.json`, with original runner/pip logs and the independent audit output alongside it.

The formal runner recorded all 7 fixed cases and 7 model decisions. No case reached its required exact action: `single_toggle` returned zero calls; the digest and timezone cases returned 3 and 4 calls respectively instead of one next action; forbidden, ambiguous, and already-satisfied cases returned zero calls; stale-generation returned two calls. The three useful nominal cases therefore had no verified effect. The four abstention/no-action boundary cases did not meet the exact required single-call contract. The auditor reports 24 semantic/tool/effect errors and four yield-boundary errors, while its structural/evidence `errors` list is empty. The fixed macro baseline exactly completes 7/7 cases with no model calls.

Cold model initialization was 4,250.148 ms. Six warm decisions had p95 10,897.878 ms (range 7,694.435–10,897.878 ms), exceeding the frozen 2,000 ms gate. The runner exited 0 after preserving a complete formal result; this means the invocation completed, not that the model passed. Peak cgroup memory was 182,272,000 bytes under a 2 GiB limit. Network and telemetry were disabled; `CUDA_VISIBLE_DEVICES=-1`; inference ran on local CPU with the pinned image/model/package hashes in `formal-result.json` and `FREEZE.json`.

## Independent audit transport note

The separate network-disabled audit container wrote a complete `audit.json`; auditor stderr is empty. The report has `errors: []`, `decision: FAIL_CACTUS_NEEDLE3_YIELD_BOUNDARY`, and independently recomputed p95 10,897.878032 ms. The outer audit shell wrapper then returned status 2 because its PowerShell-escaped `exit` argument reached `/bin/sh` as a literal backslash (`exit: Illegal number: \`). This is a wrapper/transport status defect after the report was written, not an auditor-reported evidence error. The auditor code returns success for a complete, error-free recognized FAIL decision. To honor the one-audit allocation, the auditor was not rerun; the complete report and wrapper stderr/status evidence are retained as produced.

Needle also emitted a package warning that the confidence head is uncalibrated for tuned weights; this candidate was explicitly unadapted. Confidence was not used in scoring. This warning does not change the frozen decision.

## Files

- `formal-result.json`: exact runner output, including prompts, responses, proposed calls, admissions, effects, timings and runtime identity.
- `audit.json`: complete independent audit output.
- `docker.stdout.log`, `docker.stderr.log`: formal runner stdout and the runtime warning.
- `pip-client.log`, `pip-engine.log`: exact offline installation logs.
- `audit.stderr.log`: empty auditor stderr, retained as a zero-byte file.
- `container.cid`: formal Docker container ID.
- `RESULT_MANIFEST.json`: sanitized invocation metadata and SHA-256 hashes; local absolute paths are intentionally omitted.

The smoke/construction failure remains excluded and unchanged. This result supports no broader claim about other skills, hardware, or arbitrary GUI control.
