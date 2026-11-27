# r89-a01 result

## Frozen outcome

`audit.json` reports `FAIL_OR_UNKNOWN` with exactly one failed gate: `live_container_exit_zero`. The recorded Docker exit code is 127. No retry was made.

The Calc task itself completed and was independently verified:

- The registered values were A1=`731`, A2=`864`; `verify-task.json` reports `verified` and `task_success=true` for artifact SHA-256 `9382705cdddce3bf70de1eea2e02b175b0b3883aa291ca30fbaa4abf58bd26d2`.
- The compiled method ran two transitions (`enter`, `save`), both with `release_verified=true`. The close report confirms neutral release, and the exact Calc/launcher generation exited cleanly.
- Save effect callback/request timing and same-call/attempt/process/window bindings passed the frozen auditor. The method yielded `SAFE_YIELD/effect_unavailable`; the parent verifier later proved the saved FODS effect. These are distinct receipts and both are retained.
- Both final accepted task observations (sequences 13 and 18) passed the expected Calc predicates. The frozen crop `(0,126)-(1218,742)` was pixel-identical; 691 pixels changed in the full frames outside the frozen crop.
- The compiled method elapsed time was 2,174.30 ms: enter execution interval 1,012.23 ms and save execution interval 799.63 ms. This is one candidate-branch run and has no matched conventional baseline, so it does not establish a speedup or a general latency distribution.

## Docker exit failure

The host-side wrapper captured container ID `781e7256e3efdcb94864c98b7d2559ad7c708375db1143a2d6eff6f78f00b335` and exit code 127. `container-runner.log` proves the Calc experiment completed, verifier succeeded, and cleanup completed before Bash reported `/evidence/r89-a01/runner.sh: line 27: $'\\r': command not found`. The frozen runner has CRLF at its trailing blank line; Bash treated the carriage return as a command. The runner source and exact bytes are preserved. This harness failure makes the preregistered overall result fail, even though the task/effect/lifecycle gates passed. Future preregistration must emit the runner with LF-only line endings and verify that byte-level property before launch; r89 itself is not rerun.

## Limits

One Docker/Xvfb Calc run only. No provider/model usage. No WSLc, MAP01, matched efficiency baseline, broad reliability, integrated recovery, or product-completion claim.
