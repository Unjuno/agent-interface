# Standard-caller private-Xvfb pause/recovery boundary R01

**Run ID:** `AI-XVFB-SERVER-PAUSE-BOUNDARY-20261022-R01`
**Baseline main:** `b3fdbee40cce6e9040c9a3a9360ea35cc692995e`
**Candidate commit:** `a85868f5deb36616db972b83edb591593db6986f`
**Environment:** Ubuntu 24.04 WSL2, unprivileged user/mount namespace, private Xvfb `:88`; no WSLc/Docker allocation.

## Question

Does the public standard caller return within the frozen 300 ms response target while its private X server is actually stopped, preserve `UNKNOWN`/no-replay state, then complete release and independent fresh-target task verification within the finite transaction bound after Xvfb resumes?

## Frozen conditions

Invoke once the existing standard-caller test with prestarted cancellation supervisor enabled, one-second withheld owner acknowledgement, an eight-second delayed XTest request, and an automatically resumed 1,500 ms `SIGSTOP` of only the test-owned `/usr/bin/Xvfb :88` PID. Before signaling, the test verifies `/proc/PID/exe` basename and command line display. The timer thread always sends `SIGCONT`; test cleanup and the outer wrapper also resume the exact owned PID before termination. The private socket directory is a per-run tmpfs in a private mount namespace. Use only the already present R02 dependency cache after exact version checks; no install, network fetch, WSLc, Docker, or container/image call.

The candidate includes a test-only pause hook selected by an explicit environment variable. The runtime implementation is the exact candidate branch commit above; compared with baseline main, only this integration-test file changes. Hashes of all source inputs and the candidate are preserved.

## Decision criteria

A scoped pass requires evidence the Xvfb process entered stopped state during the caller operation; caller response within 300 ms; pending response keeps release false/task success null/replay denied; the resume timer succeeds; cancellation reaches terminal within the existing 5 s test bound; independent readback observes all keys up after resume and at the delayed-request horizon; the separate fresh target/session/process generation passes the synthetic task oracle; and old cancellation remains UNKNOWN/replay-denied. Report outage and recovery timings separately. Even a pass qualifies only a finite 1.5 s process pause followed by X-server recovery. It cannot prove release while the server is unavailable, physical desktop/MAP01 behavior, owner-exclusive XTest state, reliability, or matched efficiency.

Do not retry after candidate invocation. If any preflight check fails, preserve a HOLD and do not run the candidate.
