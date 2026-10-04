# Reader SIGINT handoff construction result

Status: **FAIL (construction control only; no scientific cells run)**

The immutable `f03-reader-signal-v2` container ran the package from archive SHA-256 `00d11c5556c7c72c9a99f6d8746e834827acd712805a330dfd0142b927c85d37` against image `sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b`. It started at `2026-10-04T00:14:27.773056651Z`, finished at `2026-10-04T00:14:30.720182399Z`, exited 1, and was not OOM-killed. The full unmodified `docker logs` output is retained in `methods/READER-SIGNAL-v2.log`.

Result: 20/21 controls passed. `test_sigint_after_child_start_retains_stop` failed because a process-directed SIGINT could arrive after OS child creation but before `subprocess.Popen` returned its process handle into `child`; cleanup then recorded `cleanup_child_alive: null` instead of proving the child had been reaped. This is a runner-construction failure, not a formal result. No 4-cell candidate run or auditor was invoked.

Successor correction in the working tree blocks SIGINT on the runner thread for the narrow `Popen`/handle-assignment interval, then restores the prior mask only after `child` owns the handle. Host suite on that successor source: 21/21 PASS (`python3 -B -O -W error -m unittest discover -v`, 2026-10-04). This host result does not replace the failed container result; the corrected source still requires a new immutable container test and independent review.

## Successor construction retest

Commit `5fc1883ea` fixes the handoff and preserves the failed v2 log above. Five additional host repetitions of the actual SIGINT integration test passed. A fresh immutable Git archive was made from that commit with SHA-256 `4ec0e6e3f52aadd1612153a6fda902ea6dea18c97a3473830b376ba321901dbb`; the host and guest copies matched. New owned container `f03-handoff-v3-5fc1883ea`, image `sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b`, started `2026-10-04T00:20:37.026954515Z`, finished `2026-10-04T00:20:39.948152414Z`, ExitCode=0, OOMKilled=false. All 21 controls passed; the complete container log is retained in `methods/HANDOFF-v3-CONTAINER.log`.

The container used network none, CPU 1, memory and memory-swap 1 GiB, pids 128, read-only root, all capabilities dropped, no-new-privileges, UID/GID 501, and a private 256 MiB /tmp tmpfs. These are configured limits, not independently observed cgroup enforcement. This is `PASS_CONSTRUCTION_ONLY`; it neither supplies a formal 4-cell observation nor clears independent code review, final prelaunch custody review, or the production-scope exclusions above.
