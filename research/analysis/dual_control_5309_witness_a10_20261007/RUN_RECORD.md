# A10 execution record

- Allocation: `5309-WITNESS-A10-HOST-20261007`
- Frozen base/main at formal candidate preflight: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`
- Runtime: CPython 3.14.5, macOS host; OrbStack 29.4.0 was reachable but image inspect failed on containerd blob `operation not supported`.
- Construction: initial test run 2 passed / 1 failed due the expected count being written as 72 instead of 132; corrected pre-freeze construction run 3/3 passed. The design materializer ran before freeze. No formal run occurred before hashes were frozen.
- Candidate: one invocation, exit 0; candidate raw action choices SHA-256 `0419d9ae70430af8565d3e72dab8d59559247e7375484eb0f330e90b3ef56193`.
- Environment: one invocation, exit 0; raw SHA-256 `ad618d38ef48592d2da1a944f9400095f9dccd9a407629113724f6ad3903d834`.
- Frozen auditor: one invocation, process exit 0; report verdict `FAIL_AUDIT`, 264 reconstructed, zero row errors. Audit output SHA-256 `b6456911ebb9cade0c6f9c53e03a3cd24b646a2caace796151eefece7f6a43ef`.
- Read-only retained-data audit v2: one invocation, exit 0; `PASS_RETAINED_RAW_RECONSTRUCTION`, 264/264, zero errors, zero authority grants. Output SHA-256 `b7b054706dbdfec3e580262fe3de7ba9a46c94a20c068e764c1e8a65a1fc8088`.
- Candidate retries: 0. Environment retries: 0. Frozen auditor retries: 0. V2 audit repeats: 0. Container runs: 0. No model, GUI, GPU, OS input, or network use.

The first auditor disposition is authoritative for A10 and is not overwritten by v2. The v2 check reads retained bytes only and makes no claim of execution isolation.
