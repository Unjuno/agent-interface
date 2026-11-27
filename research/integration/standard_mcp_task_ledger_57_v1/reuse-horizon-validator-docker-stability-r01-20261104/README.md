# Docker stability settings and validator smoke — 2026-11-04

## Scope

One brief, network-disabled Docker run of the synthetic Issue #57 lifecycle/reuse-horizon validator on exact current-main source `4cca6ef5d1898cf76ad54beaa91cd6a5c4834573`. No provider call, GUI input, or experiment allocation was used. The source checkout was mounted read-only. Container limits were 2 CPUs, 4 GiB memory with no additional swap allowance, and 256 PIDs.

## Environment

- Docker Desktop 4.93.0.240920; Engine 29.8.1, 8 CPUs, about 31.4 GiB reported to the daemon.
- Active WSL settings: 32 GiB memory, 8 processors, 16 GiB swap, gradual memory reclaim. The Windows host had 63.8 GiB total and about 27.6 GiB free at the recorded start.
- The WSL `docker-desktop` distro remained running after the run. The Docker CLI responded and the container exited normally on the corrected invocation.

## Result

The corrected run passed 17/17 tests in normal Python and 17/17 under `python -O`; Docker exit was 0. Test durations were 0.030 s and 0.016 s. The tests validate synthetic ledger accounting, phase coverage, usage completeness, attempt lineage, correctness-qualified break-even, and failure handling. They are not a live agent efficiency result or proof of long-term Docker stability.

The first invocation also ran both suites successfully and retained their raw logs and `exit-status.json`, but the Windows-generated CRLF shell script caused its final `exit` command to receive a carriage return and Docker returned 2. The corrected LF script and separate raw rerun files preserve the repair and successful result; the initial run is not counted as a Docker pass.

## Files

`conditions.json`, `runtime-after.json`, and command/script files pin the host configuration, image digest, source commit, container bounds, and invocation. Normal/optimized stdout and Docker exits are retained per invocation. `source-files.json` pins the relevant Git blob IDs. `SHA256SUMS.txt` covers every other file in this packet.

Reproduce from the repository root using the command in `command-rerun-01.txt`.
