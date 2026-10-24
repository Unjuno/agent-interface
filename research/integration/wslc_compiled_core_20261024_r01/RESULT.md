# WSLc compiled-control core R01

**Disposition: PASS for the frozen local control-core checks only.** On commit `5e378a416bd083609f1a9f5b4b9ade3fad9a584d`, CPython 3.14.8 in the locally cached WSLc image `a09-owner-close-xvfb:20261012` ran the current compiled-GUI boundary and malformed-release recovery unittest modules: 37 tests passed in 0.008 seconds.

The checks cover bounded observation/admission/execution/effect timing, stale or ambiguous state refusing another dispatch, conservative release handling, and preservation of verified prefixes when a later release receipt is malformed. Source hashes, the exact command, stdout/stderr, full container ID, and cleanup receipt are retained under `run/`. WSLc used `--pull never`, `--network none`, one CPU, a requested 768 MB, a read-only repository mount, and an attempt-scoped raw-output mount. `--rm` ran, and a filtered query for the full container ID returned no match.

The kernel reported that swap/cgroup memory limits are unavailable, so the requested memory limit is not treated as a verified hard ceiling. These tests use deterministic drivers and do not exercise MCP, Fake X/server composition, WSLc GUI, native Win32, physical input, MAP01, a real application task effect, efficiency, or reliability.

This pass advances only the software contract under WSLc. The separate Fake X standard-caller attempt R01 failed before its test body because the local image lacks the MCP SDK; that failure is preserved separately and was not retried.

Conditions and raw logs are retained in this directory. `SHA256SUMS` covers every packet file except itself.
