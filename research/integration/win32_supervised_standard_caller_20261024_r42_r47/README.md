# Win32 supervised standard-caller attempts R42–R47

This rollup indexes six distinct, one-shot native-Windows fixture attempts. Their raw results remain attempt-specific; do not combine them into a reliability rate or substitute a successful attempt for a failure.

| Attempt | Disposition | Evidence and limit |
|---|---|---|
| [R42](../win32_supervised_standard_caller_20261024_r42/RESULT.md) | Phase 1 strict release gate 11/11; paired attempt FAIL_OR_UNKNOWN | Q-up was independently observed during the 1,262.5311 ms callback hold. Phase 2 stopped on a harness `NameError` before public dispatch or task input. |
| [R43](../win32_supervised_standard_caller_20261024_r43/RESULT.md) | PASS_SCOPED, separate task-only attempt | Independent server oracle verified the exact fixture effect for a new generation. It was not paired with R42's release attempt. |
| [R44](../win32_supervised_standard_caller_20261024_r44/RESULT.md) | PASS_SCOPED, one paired attempt | Strict release gate 11/11, then a separate-generation task oracle passed 12/12. |
| [R45](../win32_supervised_standard_caller_20261024_r45/RESULT.md) | FAIL_OR_UNKNOWN | The callback hold measured 1,245.0446 ms, 4.9554 ms below the frozen 1,250 ms gate; phase 2 correctly did not start. |
| [R46](../win32_supervised_standard_caller_20261024_r46/RESULT.md) | FAIL_OR_UNKNOWN, paired attempt incomplete | Phase 1 passed 11/11; phase 2 failed before fixture startup because the runner invoked a script path with `python -m`. |
| [R47](../win32_supervised_standard_caller_20261024_r47/RESULT.md) | PASS_SCOPED, one paired attempt | Strict phase 1 passed 11/11 at a 1,405.5285 ms hold; a distinct-generation task oracle passed. Fixture write-return to oracle-read observation was 253.5745 ms. |

R42–R47 ran on the local Windows fixture path. The `task_success=true` claims are independent server-oracle results; runtime-integrated `task_success` remains null. The reported write-to-oracle interval is not physical durable-storage latency or a physical input-to-effect interval.

PR [#9502](https://github.com/Unjuno/agent-interface/pull/9502) subsequently closed the R47 crosswalk's missing synthetic composition check: it drives `compiled_gui.run()` through the public supervised Win32 dispatch/results route and verifies fail-closed suffix refusal after target-generation change. That construction check does not change any R42–R47 live result.

The six attempts do not establish MAP01, a real-application transfer, WSLc allocation eligibility or GUI behavior, matched efficiency, or broad reliability. WSLc remains STOP/HOLD under [Issue #7924](https://github.com/Unjuno/agent-interface/issues/7924).

## Publication and custody

Public `SHA256SUMS_PUBLIC_R01` manifests cover each retained packet's current published files. Original experiment manifests and raw evidence remain unchanged where present. Generated Python bytecode and local-only test output were retained in the local custody directory and excluded from publication. R46's path-bearing stderr is retained privately; the public packet contains an explicitly labeled redacted explanatory copy. The private excluded-file SHA-256 manifest is outside the Git worktree.
