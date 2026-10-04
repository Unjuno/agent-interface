# First formal run

## A01 first formal outcome — STOP_FORMAL_OUTPUT_DIRECTORY_PREEXISTED

The frozen candidate received its one permitted WSLc invocation at 2026-10-04 03:09:55 UTC and exited 1 at `Path('/out').mkdir(..., exist_ok=False)`: the PowerShell runner pre-created the mounted output directory, while the candidate contract expects the mount root itself not to exist. No candidate rows/images/manifest were emitted. The auditor was not invoked. A01 is terminal; retries=0. This is an execution-contract STOP, not a scientific result or test of the Issue hypothesis.

The host's cgroup/swap warning was emitted and is retained. WSLc's `--rm` returned the named candidate container to absent state; the active-container list was empty immediately after. The external output mount was created by this task and remained empty. No pre-existing container or image was modified.

Captured combined WSLc output is in [A01_FIRST_OUTPUT.txt](A01_FIRST_OUTPUT.txt), and the command, exit, raw byte inventory, and scope are in [A01_FIRST_OUTCOME.json](A01_FIRST_OUTCOME.json). The original freeze and source hashes remain unchanged.

Any continuation needs a fresh allocation and source freeze that accepts an already-existing empty mount root (or uses a new child path), separate from A01. Do not reuse any A01 output or timing, and do not call the current frozen candidate/auditor again under A01.
