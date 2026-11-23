# A01 amendment — invocation setup correction

The first wrapper invocation launched both Python processes from `worktrees/` instead of the frozen repository root. Both failed to import `runtime` before the target unittest loaded; the tool output records exit 1, stdout 0 bytes and stderr 707 bytes in each mode. A normal-mode traceback was displayed and showed `ModuleNotFoundError: No module named 'runtime'`.

The original setup stderr files were overwritten by the corrected run before they were copied into separate retained files. Exact initial bytes are therefore not in this packet; `SETUP_ERROR_TRANSCRIPTION.txt` preserves the observed summary and traceback excerpt, explicitly as a transcription rather than raw output. This custody deviation is retained.

A01 uses the same frozen target and source commit but fixes only the wrapper working directory to the repository root (`packet.parents[3]`). It runs exactly one normal and one `-O` process in the original fixed order, with no retries/replacements after either target test begins. Any target-test failure remains in the denominator.