# #5156 local Docker entrypoint/argv construction — v2 successor

## H/T/D/C/U

**H.** A container with no `Entrypoint` and `Cmd=["python3"]` will replace that default command when a script path is supplied directly, causing an exec-format failure. Explicit `--entrypoint python3` plus a script-path argument produces the intended interpreter argv and allows dependency preflight before the smoke runner.

**T.** Freeze the exact image config, command vector, local image digest, candidate, auditor, and input. Run five Docker construction tests. Then invoke one harmless smoke candidate through explicit `--entrypoint python3` with no shell; audit raw output in a separate container. Include the previous STOP as immutable predecessor evidence, not as a rerun.

**D.** `PASS_LOCAL_ARGV_CONSTRUCTION_ONLY` requires five construction checks; candidate process argv exactly equal to the frozen resolved argv; the declared standard-library dependency imports before one harmless callback; and a separate raw-only audit with zero errors and zero formal/GUI/network/model calls. Candidate/argv mismatch or callback before preflight is FAIL.

**C.** This local image is amd64 and has no entrypoint plus default command `python3`. This is not the Allocation 04 arm64 image and does not test Xlib, Xvfb, the owner runner, input delivery, or GUI effects.

**U.** Only command construction and generic interpreter/preflight order are measured. No formal #5156 allocation is consumed or authorized. The eventual X11 run still requires fresh coordinator allocation, exact target image and dependencies, current source freeze, one invocation, and independent raw audit.

## Provenance

Frozen GitHub main: `241a0cac915df615f7f79b4ce2042b946ea7fbd7`.
Docker Desktop Engine 28.5.1; image `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, `linux/amd64`; inspected config `Entrypoint=null`, `Cmd=["python3"]`. Network none; source read-only; output-only writable mount.

Predecessor `ENTRYPOINT_ARGV_CONSTRUCTION_5156_T0_20261001_01` remains STOP evidence under `_scratch_5156_argv/`; its freeze is not edited and its failed invocation is not retried.
