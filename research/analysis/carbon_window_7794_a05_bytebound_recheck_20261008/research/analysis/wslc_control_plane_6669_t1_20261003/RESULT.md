# T1 result: WSLc control-plane under bounded pressure

Allocation: WSLC-CONTROL-PLANE-6669-T1-20261003-A01. Based on main `e7f11cdc2cdee42b0f745add6c4a93fc641abe6d`. Runtime WSLc 3.0.1.0, SDK Microsoft.WSL.Containers 3.0.1, WSL kernel 6.18.40.1-1. Experimental session `codex-wslc-audit-6669-20261003` was distinct from the user's default session, configured with CPU=1 and memory=1024 MiB. Session/container inventory was checked before every candidate. Image: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`.

## Conclusion

**PASS, narrowly scoped:** during the instrumented 640 MiB candidate's 60-second hold, WSLc info, session list, container list, stats, logs, stop, inspect, remove, and post-removal absence checks all returned exit code 0 within 15 seconds. The candidate independently recorded receipt of SIGTERM (15), exited 0, and was removed. The first control command started 14.328 seconds after the pressure-ready sample; stop took 161 ms. The three raw-data mutations (false success, missing stop acknowledgement, missing cleanup) were all rejected by the standalone auditor.

This demonstrates control-plane operation for one isolated WSLc 3.0.1.0 session under the preregistered synthetic memory-pressure condition. It does not demonstrate hard per-container memory enforcement or a general OOM safety guarantee.

## Evidence

The pressure candidate allocated and touched exactly 640 MiB in 8 MiB steps; it reported guest `MemTotal=922048 kB`, `MemAvailable=99564 kB` at pressure-ready and 98076 kB when SIGTERM arrived. This crosses the preregistered <128 MiB pressure threshold. Container stats sampled 652.3 MiB / 768 MiB. cgroup `memory.max=805306368`; all `memory.events` counters were zero. `memory.swap.max=max`, and WSLc warned that swap limit capabilities were unavailable. Therefore this run provides no evidence that the container memory cap would kill or contain a workload beyond the tested allocation. The session VM cap, not the per-container flag, was the isolation ceiling.

The matched 32 MiB no-pressure candidate with the same SIGTERM handler stopped in 124 ms and exited 0. Earlier instrumented-free Python PID 1 candidates took about 10.17 seconds and exited 137 in both pressure and no-pressure runs. That was a test-process signal-handling confound, not evidence of a WSLc pressure-specific defect. Linux PID namespace documentation explains that an ancestor can signal namespace PID 1 only when it has installed a handler for that signal: https://man7.org/linux/man-pages/man7/pid_namespaces.7.html

No GPU, Docker runtime, shared-session container, network access from candidate containers, GUI workload, or shared-host pressure was used. This was a synthetic CPU/memory experiment and does not generalize to model workloads.

## Reproduction and audit

See `FREEZE.md`, `AMENDMENT-01.md`, `AMENDMENT-02.md`, `AMENDMENT-03.md`, `candidate-sigterm.py`, `audit-final-v3.py`, and `audit-mutations-v3.py`. Raw candidate logs and every control command result are preserved alongside SHA-256 hashes in `SHA256SUMS.md`. The experiment and results were posted to issue #6669 before this PR.
