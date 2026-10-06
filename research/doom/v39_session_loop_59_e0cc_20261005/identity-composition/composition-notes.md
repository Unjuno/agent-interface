# Private identity/frame-barrier composition

This package composes the #8031 observation-identity repair into the current resolved #8094 controller snapshot without modifying the owned checkout. It is a source candidate only; no controller, owner, child, or integration tests were run.

## Inputs and identities

- #8094 owned checkout: `/Users/taka/Documents/Codex/2026-10-03/new-chat-6/work/perkey-owner-guard-repo-e0cc-20261005`, `HEAD=88e8099de97de12c29fcf3db0cb374b160a27ead`.
- Resolved current controller copied from the owned checkout working tree and staged index. Both have SHA-256 `2dde68aabd9b4f014c5bceaa7839aef363d7439e7f11b75494fe7ee1c856d6a9` before composition. The source retains #8094 stale-renewal/no-active-cover behavior and the completed/expired neutral-terminal race handling.
- Current main test source copied from the staged index: SHA-256 `7f43877c154c80ab80c73cbe7acbae49a1d798242c0835bde2105526566d9835`. The candidate copy keeps those assertions, including `completed` and `expired` terminal releases, with only its import path redirected to the candidate source.
- #8031 identity source: commit `78da45acb3b1aff7200a66e63c02b9808f622c02`, parent `d3a51bc4c962b223d05280225042b96a033df8bf`.
- #8094 base `observable_signal_guard_v2.py` was read from its `HEAD` object: SHA-256 `7be055c4bd68a1528f4b2b02b543435bd64465ea42d4452f5597d6dce08442a0`.

## Composition

`composition.patch` adds the #8031 monitor identity preservation (`capture_ns`, detached `pointer_binding`, optional `frame_rgb_sha256`) and V39 `wait_for_invalidation_frame` helper/call. It waits after the invalidated planner result and before recording/continuing to a later planner turn. It preserves #8094's existing cancel/terminal routine unchanged, including acceptance of `cancelled`, `completed`, or `expired` only with verified empty keys and buttons; it also leaves the renewal rejection and `current_cover is None` paths unchanged.

The candidate also applies the same identity barrier to the initial-cover invalidation branch before its `continue`. This is a composition-specific extension beyond #8031: without it, a `typed_observation` can invalidate the initial cover while `latest` still points to the prior RGB observation, and the next iteration can start from that old frame. The branch retains the prior `source_image` for provenance and records the matching `invalidation_frame_image` separately. The current test copy gains a source-order assertion for this branch; it is not behavioral test evidence.

The candidate test tree keeps the current #8094/main45 test file, and separately carries the #8031 pending hard/unknown invalidation, wrong-binding/stale-capture/fresh-frame, and detached-identity tests. Imports in the copied identity tests point at the candidate controller/monitor. These are test-source copies only, not test results.

## Checks and limits

`ast.parse` succeeded for all eight Python files under `base/`, `candidate/`, and `tests/`. No tests were executed. This checks syntax only; it does not establish that the composed pending/no-active-cover loop and identity barrier work together under the real child process. The root-owned real subprocess harness remains the next validation boundary.

## Candidate hashes

- Candidate V39 controller: `69c691d8c4413839d0673605215064efa3091174c390c8ef8494c19bdf0523a9`.
- Candidate signal monitor: `a93ec77e6ae9c9132656927752b443a3cd4864d4418d4bddbde5ba33fbdb4e3a`.
- Current #8094/main45 test copy (imports redirected only): `c09d59a80262f58bff4fc45d14a57e118696a74643cb12c6a9074fce10743e3f`.
- Separate #8031 pending invalidation test copy (candidate imports redirected): `9d52793eb6978424a93d11c707cf2e129b25f273b9d8210e60b4cf8133b778de`.
- Current signal-guard test copy with identity mutation tests: `1de92d88eccf90d30401aa7d57435580bc80daf7b1f79f4d0c129cf3e57c484c`.
- Separate #8031 signal identity test copy: `2cad9838ddf56cec4867357daa00fa9b789dcb1e1880c5311b367f2a556cb0ae`.
