# A01 amendment — invocation setup correction

The first wrapper invocation launched both Python processes from `worktrees/` instead of the frozen repository root. Both failed to import `runtime` before the target unittest loaded; stdout/stderr/exit/timestamps are retained as `setup-error-normal.*` and `setup-error-optimized.*` after the corrected run. These were harness setup failures and are not scored as target-test samples.

A01 uses the same frozen target and source commit but fixes only the wrapper working directory to the repository root (`packet.parents[3]`). It runs exactly one normal and one `-O` process in the original fixed order, with no retries/replacements after either target test begins. Any target-test failure remains in the denominator.