# WSLc Fake X standard-caller attempt R01

**Disposition: FAIL_OR_UNKNOWN for the composed caller test; WSLc cleanup PASS.** One uniquely named container was launched from the locally cached `a09-owner-close-xvfb:20261012` image with network disabled and the repository mounted read-only. The pinned image ID matched the frozen condition. Python 3.14.8 failed while importing `runtime.cli_v1.test_mcp_relay_composition` because the image lacks the `mcp` package. No unittest case body ran, so no Fake X input/effect, target-generation receipt, cancellation, or task result was produced.

The command exited 1 in under one second. WSLc wrote full container ID `5262d6eeaf3e33d7f266a6a65db8858474088c2d73c42e64b7d82ab45fc504c0`; the exact-ID filtered post-run query exited 0 and returned no container. The run used `--rm`, `--pull never`, `--network none`, one CPU, requested 768 MB, and an attempt-specific output mount. The kernel reported that swap/cgroup memory limits are unavailable; memory enforcement is not claimed.

No retry was made. This result identifies the concrete blocker: the available WSLc image cannot import the MCP caller test dependencies. The separate compiled-core packet records a successful dependency-free WSLc verification. Neither packet establishes WSLc GUI, physical input, MAP01, live provider behavior, efficiency, or reliability.

Conditions and raw logs are retained in this directory. `SHA256SUMS` covers every packet file except itself.
