# Issue #3311 termination-report Docker successor — allocation 03

## H / T / D / C / U

### H — hypothesis

The retained termination-report supervisor can preserve correct RETAIN/HOLD/STOP distinctions and immutable evidence across child-process failure, missing reports, source-pin mismatch, and path/digest mutation when run as an offline containerized contract suite. A pass is only supporting evidence that a future #3311 run can be classified safely; it is not the integrated efficiency result.

### T — bounded test

Run the exact unchanged 13-test `issue3311_termination_report_v2/test_supervisor.py` suite once under a Docker Desktop container pinned to the locally cached Python 3.12.14 image digest. Network is disabled; source is read-only; only `/out` is writable; the container root is read-only with bounded tmpfs, CPU, memory and PIDs. A pre-frozen wrapper verifies source digests, executes the test suite once, retains per-test artifacts and stdout, and invokes a separate raw-output auditor. No model, GUI, task input, or shared GPU/container service is used.

### D — decision

`PASS_TERMINATION_HOLD_CONTRACT_DOCKER_SCOPED` only if all 13 named tests run and pass, source digests match, all 13 per-test artifact directories exist, the independent auditor accepts the raw result, and the container exits zero. Any assertion or audit mismatch is `FAIL_TERMINATION_CONTRACT`; source/image/runtime/output precondition mismatch is `STOP_CONSTRUCTION_OR_PROVENANCE`. Preserve the first execution exactly; no retry or post-result tuning.

### C — controls

The suite covers complete RETAIN, missing sixth task row to audited HOLD, source-pin mismatch, unlaunchable child to STOP, misleading failure text not becoming REJECT, zero exit with absent report, preservation of valid scientific disposition/report, disagreeing audit to HOLD, existing terminal/result bytes not overwritten or reused, raw digest mutation rejection, path-traversal rejection, and the frozen runner's report timing boundary. All subprocesses run inside the isolated container.

### U — limits and stop conditions

This Docker successor deliberately differs from unexecuted allocation-02's Windows CPython 3.11.9/no-container environment because that exact interpreter is absent locally and Docker images. It therefore does not validate Python 3.11.9 parity. The supervisor cannot persist a record if itself/OS is forcibly killed. No live desktop, model, task/effect, latency, token, efficiency or product claim follows. Issue #3311's cold/warm/invalidation/repair comparison and #57/#2068's end-to-end model-facing comparison remain open.

## Frozen runtime

The exact image digest, platform, Docker Desktop version, context, resource controls, source hashes, command, output contract, and test list are recorded in `FREEZE.json`. The runner and auditor are part of the frozen source set. Any mismatch before invocation is STOP; do not tune and rerun this allocation.
