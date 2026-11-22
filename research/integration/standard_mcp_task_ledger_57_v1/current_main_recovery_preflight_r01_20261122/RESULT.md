# Current-main Win32 recovery preflight R01

**Disposition: `PASS_LOCAL_RECOVERY_PREFLIGHT_ONLY`.** On main source `77d3a4bb704b68868b86208674aded55b5f2cacf`, `runtime.cli_v1.test_mcp_supervised_win32` passed 59/59 normally (123.350 s) and 59/59 with `-O` (130.876 s), exit status 0 in both modes. Exact output is preserved under `raw/normal/unittest.log` and `raw/optimized/unittest.log`.

The frozen five-source runtime fingerprint in `conditions.json` matched the current-main runtime tree during the trial.

## Scope

This is a local Fake/contract preflight before designing a fresh standard-caller recovery task. It did not dispatch input to a live target, call a model/provider, consume a WSLc or Docker allocation, or test a real expiry/recovery event. It is not a recovery success, task-success result, reliability estimate, MAP01 outcome, efficiency comparison, or Research Preview acceptance.

The next experiment remains separately frozen: induce a bounded pre-dispatch/held-input failure in the standard caller, capture old-generation refusal and release/neutral horizon, distinguish exact task effect and timing eligibility, and obtain an independent task oracle. Historical Win32 R09 remains a reference only; this Fake suite does not replace it or establish current-main live recovery.

## Custody

`conditions.json` pins the main SHA, interpreter, commands, scope, acceptance criteria and source hashes. The raw test logs are unmodified command output. `raw/SHA256SUMS.txt` covers the two output logs; root `SHA256SUMS.txt` covers all packet files except itself.
