# Admission-baseline callback failure repair A02

A02 rechecks the A01 baseline-failure boundary against the latest ExecutorV12 and ExecutorV13 source on PR #7429. It injects failure in the accepted-event callback, then verifies that neither executor starts input and that shutdown does not join an unstarted worker.

Use [PLAN.md](PLAN.md), [FREEZE.json](FREEZE.json), and `SHA256SUMS.txt` for the frozen hypothesis, source, and run gates. The candidate is one-shot and already executed. This is fake-backend host-Python construction evidence, not a real scorer callback or live recovery test.
