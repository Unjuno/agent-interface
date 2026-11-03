# Private display draft: pidfd acquisition failure and subsequent reap

If `pidfd_open` failed after Xvfb was spawned and the first termination wait timed out, the preceding draft retained the child object but its later `close()` rejected the missing pidfd and could not reap it. A controlled local test injected both failures and reproduced this before the change; that initial console output is not included in the archive.

The draft now records when startup cleanup has already requested termination or observed the direct child exit. If no pidfd was obtained, a later retirement can wait for that already-signalled child; it does not send another PID-based signal. It marks the child retired only after `wait()` returns. The test injects `pidfd_open` failure and one wait timeout, restores the real wait, and confirms the retained child can subsequently be reaped. The injection is not proof of behavior under all kernel failures or concurrent reapers.

Seven tests passed in each of two new WSLc containers, normal Python and `-O`, using pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`, one CPU, a 1 GiB memory limit, no network and no pull. WSLc reported swap was not limited. [raw.zip](raw.zip), SHA-256 `99ce931c36fc2ca7b3628d7bc6f771e6d6d474a837e67ee8c21998585bb429c3`, retains the candidate, tests, hashes and outputs.

The implementation is still a draft. Concurrent retirement and close, other process/fd failure points, timeout validation, cookie lifecycle, resource exhaustion, broader suites and cancellation/MCP integration remain unverified. A pending close needs a later completion check; no physical input release, end-to-end recovery, MAP01 completion or hard deadline is established. Earlier held-key composition used a previous revision.
