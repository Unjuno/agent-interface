# R01 disposition

R01 stopped in preflight before starting Edge, OCR, or a form action. The
runner used `HERE.parents[2]` as the Git root even though that path is the
worktree's parent; `git status --porcelain` exited 128. The local server had
been started but the test's outer `finally` shut it down. No task input, model
call, screenshot, POST, or result was produced. This is a harness construction
failure, not a scored task attempt.

The path fix and new output location were frozen separately in R02, whose
preflight then stopped on a second path-component error before Edge startup.
No gate or pass condition changed. R01 is retained unchanged as a failed
preparation.
