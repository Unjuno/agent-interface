# Report — OS-backed scorer-tail readiness under callback overrun

**Behavioral disposition: `FAIL_OS_READY_COMMAND_STARVATION_ON_SAMPLE_OVERRUN`, reconstructed by the independent audit.** The candidate raw's own disposition remains `INCONCLUSIVE_OR_DIFFERENT_SOURCE_BEHAVIOR`; its classifier failed to treat the adapter's `deadline_overrun` terminal as meeting the preregistered “at/after deadline” criterion.

On Windows 10 build 26300 with CPython 3.11.9, the frozen adapter used a real socketpair receiver, `select.select`, and `time.perf_counter_ns`. The fast control had a 1 ms callback, one scorer row, one readiness poll, and returned `command_ready` with all 16 bytes still unread. In the two 25 ms callback cases, the socket contained a ready command before the first callback or became readable 5 ms into it. Both cases ran four scorer rows over approximately 101 ms, made zero readiness polls, returned `deadline_overrun`, and retained all 16 command bytes. The result confirms the source-boundary liveness gap under OS-backed descriptor readiness.

The audit verified all four frozen source hashes, clock-domain consistency, source pin, fast control, both starvation cases, and the frozen gate facts (6/6). Four tests reject mutations to the ready control, unread bytes, and readiness count. The audit also detects the candidate's disposition mismatch rather than silently correcting the raw.

Three earlier construction invocations stopped on Windows `MSG_DONTWAIT` portability or cross-thread readiness setup. A fourth completed with zero samples because a timestamp-zero synthetic release receipt was in a different epoch from `perf_counter_ns`; its result is retained and excluded. The fifth, unregistered exploratory run showed the same behavior but occurred before a valid freeze and is excluded. These are fully listed in `RUN.md`.

This construction does not test console stdin semantics, the DoomGame owner thread, actual command handling, keyboard release, model behavior, game effect, useful feedback, task recovery, safety, performance distribution, or MAP01 completion. No live allocation or shared runtime was used. PR #7692 head was read back from `refs/pull/7692/head` as `0c3627d63072b89d1c769fd0048e93baf157f5c7`; it matches the source revision tested.

**Implementation implication:** check command readiness before every scorer callback, including when a previous callback overruns the next sample deadline, and preserve the current rule that the tail returns without consuming command bytes. Add ready-at-entry and during-overrun regressions. The adapter itself is not changed in this evidence package.

