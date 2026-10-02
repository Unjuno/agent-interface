# Allocation A01 disposition

Candidate invocation 1/1 exited 1 before writing `candidate_result.json`. In cwd `/tmp/run`, the entrypoint `python select.py` inserted that directory as `sys.path[0]`; `platform.platform()` attempted `subprocess`, which imported `selectors` and resolved the local `select.py` instead of stdlib `select`. The failure is independently classified from the retained raw trace.

This is `FAIL_RUNNER_IMPORT_COLLISION_NO_METHOD_RESULT`, not an evaluated selector outcome. The mathematical auditor ran 0 times because its required candidate result was never emitted. A separate post-hoc trace classifier ran once in a distinct container; its stdout and hash are retained in this directory. A02 Issue #6744 isolates the import path and uses separate evidence.
