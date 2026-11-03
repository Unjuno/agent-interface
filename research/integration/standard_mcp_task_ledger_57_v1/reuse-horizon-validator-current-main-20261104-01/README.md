# Reuse-horizon validator current-main rerun — 2026-11-04

## Scope

This is a reproducibility rerun of the synthetic comparison validator on exact current main `1db2df19bbc311bfd77df97e7223274480aaf6ac`. It does not measure an agent route, call a provider, send GUI input, or estimate end-to-end latency or efficiency.

## Result

The pinned offline Docker image `agent-interface-xvfb-mcp:late-input-r19` ran `test_comparison_measurement_v1` against read-only current-main source with 2 CPUs, 4 GiB memory, 4 GiB total memory+swap, 256 PID limit and no network. Normal and optimized Python each passed 17/17; both exits and Docker exit are 0. Per-test output and exit records are retained here. The host engine was Docker 29.8.1 with the active `.wslconfig` snapshot 32 GB / 8 CPU / 16 GB swap / gradual reclaim.

This confirms the validator's synthetic coverage for matched conditions, phase timing, plan-attempt lineage, retries, terminal cold/repair outcomes, unavailable usage, and correctness-qualified break-even. It does not prove a live comparison or that Docker's stability settings prevent crashes.

## Construction attempt

During evidence packaging, one PowerShell command-string split the Docker mount option incorrectly. Docker rejected that invocation before creating a container (exit 125). The command and output are retained as `launch-failure-*`. The exact argument-based rerun then passed as recorded in `command.txt`, `docker-run-output.log`, and `docker-exit.txt`; the failed launch is not counted as a test result.

## Reproduction

From repository root, run the command in `command.txt`. `run.sh` writes the normal/optimized raw logs and their exit status to the mounted evidence directory. `SHA256SUMS.txt` covers every retained file other than itself.