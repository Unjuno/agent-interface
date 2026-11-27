# Public-caller Fake X bystander refusal check

**Result:** PASS, scoped, in normal and optimized CPython.
**Source:** `cdc8bd6b65bf976137db645c2be31e20090f7d67` (`origin/main` matched at run time).
**Host:** Windows host, CPython 3.11.9.
**Test source SHA-256:** `b6cd8774fec60390f0da41f2d050119cac13f5c6bc7bb80498066967dbb5810f`.

The focused test `runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_prestarted_supervisor_public_path_preserves_bystander_refusal` passed in normal mode (2.894 s) and optimized mode (2.814 s). The test asserts that an unrelated Fake X client reusing the resource base is rejected as `resource_base_reused_by_unrelated_client`; the release attempt is `not_attempted`; fake key state remains down; no input effect occurs; cleanup remains `UNKNOWN`; runtime task success remains null; replay is denied.

This complements the R02 live-Xvfb positive path that permits the supervisor's own resource-base reuse. It is only a synthetic Fake X public-caller check. It does not establish the same bystander rejection on Xvfb or another live X server, real physical release, task success, WSLc portability, MAP01, reliability, or matched efficiency. No WSLc or Docker allocation was used.

Raw output, exact commands, conditions, exit codes, and hashes are in `raw/`.
