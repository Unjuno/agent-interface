# A03 runner construction record

The frozen A03 v1 runner did not start either arm. It exited at import time because the copied launcher looked for `probe.py` inside `a03_post/`; the pinned A01 helper resides one directory above. The failed command and traceback are preserved in `TOOL_STDOUT_A03_CAPTURE.txt`. No baseline/candidate code executed and no A03 result directory was created.

A versioned v2 runner changes only the helper import to the parent evidence directory and writes to a new `results/a03_v2/` path. The scientific schedule and decision rule remain unchanged. The exact v2 bytes and protocol are frozen separately before execution; v1 is not edited or rerun.
