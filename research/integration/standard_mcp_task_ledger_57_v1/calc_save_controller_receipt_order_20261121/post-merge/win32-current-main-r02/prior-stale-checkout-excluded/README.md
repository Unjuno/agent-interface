# Excluded prior attempts

These logs came from the existing `897f4896`-based worktree, which was 66 commits behind `bc7e62ed`. Although the focused artifact and composition files matched current main, surrounding runtime files did not. They are retained as observed exploratory outcomes and excluded from the current-main result; do not use them as a current-main failure.

- `windows-normal-fail.log`: failed with `trusted_save_controller_unavailable`.
- `windows-optimized-fail.log`: failed with `trusted_save_controller_unavailable`.
- `receipt-trace-normal-inconclusive.log`: an instrumented rerun failed earlier during owner cleanup (`resource_base_unavailable`) and never reached the receipt builder.
- `trace_receipt_builder.py`: the temporary read-only diagnostic used for that inconclusive attempt.
