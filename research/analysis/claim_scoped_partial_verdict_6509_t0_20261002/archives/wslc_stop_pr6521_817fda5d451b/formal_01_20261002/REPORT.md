# T0 formal allocation — stopped

The formal allocation did not reach the construction gate. The only WSLc invocation ran the pinned runtime probe and returned exit 0, but the preregistered one-shot construction command also required `python -B -m unittest -v test_protocol`; that suite was accidentally omitted. Since the freeze allows one construction invocation and zero retries, the rung is consumed and the allocation stops here. Candidate and auditor were not run.

WSLc emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The container nonetheless reported Python 3.12.14 and cgroup `memory.max` of 1073741824 bytes. These runtime observations do not repair the missing construction tests and do not count as a method result.

This is an execution/protocol failure, not positive or negative evidence about claim-scoped partial verdicts. The host-side 11-test construction check and earlier in-memory toy check are development-only, non-formal evidence. No live-system, latency, or safety claim is made. The stop was reported on GitHub Issue #6509; see the linked branch and retained raw output paths in the comment.
