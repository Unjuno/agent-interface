# A07 preregistered test: actual cleanup regression suite in isolated WSLc

**H.** The PR #8687 cleanup implementation rejects ambiguous repeated accepted IDs and repeated terminal IDs under the actual class API, while current main exposes these regressions. This should hold in normal and optimized Python execution.

**T.** Freeze current main `f185a9059d485a4f8d5a65e9e7f6782897f67eae` source blob and PR #8687 `6195600931fa6de4ecf1a5012cb83b549addb5af` source plus its focused regression module. In one WSLc Python container, execute the PR's five-test module against both frozen implementations under normal Python and `-O`; network disabled, one requested CPU, 512 MiB requested memory. Capture raw unittest output, exit code, runtime version, and visible cgroup limits.

**D.** PASS_SCOPED only if both candidate runs pass all five tests and both current-main runs fail exactly the two duplicate-identity tests, with no other test failures. Any other pattern is FAIL_SCOPED; a changed/mismatched source blob or unavailable container is HOLD.

**C.** These focused cleanup tests may omit interactions in the whole controller, event producers, or integration path. Python optimization is a second execution mode, not a separate runtime.

**U.** This is a local API/cleanup regression test only. It does not exercise the full controller main loop, physical key release, GUI/game, model, useful feedback, bounded recovery, or live threat response. It does not rerun A05's formal allocation/auditor and cannot establish end-to-end computer-control success.
