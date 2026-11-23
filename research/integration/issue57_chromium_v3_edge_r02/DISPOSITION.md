# R02 disposition

R02 stopped before Edge or OCR. A path in the test harness created its raw
directory at `<worktree>/integration/...` but looked for frozen protocol and
auditor files at `<worktree>/research/integration/...`; source hashing failed
with `FileNotFoundError`. No browser was launched, no task input or model
fixture was used, and no POST occurred. The accidentally created sibling raw
directory was empty and removed.

R03 corrects the output path and adds an explicit no-action preflight before
the one-use UI procedure. R02 is retained as a failed preparation.
