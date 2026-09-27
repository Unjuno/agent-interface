# Container X11 recovery transfer v1 prereg construction failure

Status: **RETAINED PRE-EXECUTION FAILURE; NO FORMAL SCHEDULE EXECUTED.**

The v1 held-out transfer runner and preregistration were frozen before any formal schedule was executed. The final preflight then found that `run_formal()` began with `shutil.rmtree(root, ignore_errors=True)`. Although the intended one-shot output path was absent, this implementation would permit an accidental later rerun to delete and replace the first formal result. That violates the stated first-result/no-retry evidence policy.

Disposition:

- v1 formal allocation: **NOT STARTED**;
- v1 formal output: absent;
- v1 schedule outcomes: unobserved;
- no threshold, schedule, recovery rule, planner delay or efficacy gate was changed in response to data;
- v2 may change only formal-output lifecycle from delete-and-recreate to fail-closed `FileExistsError`, use a new output path/version, freeze new code hashes, and then execute once.

This failure is retained because a preregistration that can silently overwrite its own first result is not an acceptable experimental contract, even when the first output does not yet exist.