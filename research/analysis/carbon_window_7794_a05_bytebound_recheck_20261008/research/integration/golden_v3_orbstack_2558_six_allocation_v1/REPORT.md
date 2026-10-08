# #2558 six fresh OrbStack allocations

Date: 2026-09-20 (Asia/Tokyo)

## H/T/D/C/U

- H: the fresh model-to-native-handle path remains stable across six independent OrbStack allocations, while focus invalidation remains fail-closed.
- T: run six sequential containers from one digest-pinned local image; each container starts a new private Xvfb and fixture, captures a new image, calls host-local Codex, admits the field point through native_handle_bridge, performs the guarded action, reads an independent effect, verifies release, performs read-only continuation, then probes focus-change handle reuse.
- D: 6/6 task effects succeeded; 6/6 visual target revalidation true; 6/6 release verified; 6/6 continuations completed without input replay; 6/6 focus-change probes refused with `SCOPE_MISMATCH` and emissions delta 0. Effects were `docker2558-six-task-1` through `-6`. Action-to-scored-effect mean 151.695ms, median 153.220ms, range 144.181–157.900ms. Model calls executed for all six tasks; usage was recorded per task in the raw run directories.
- C: `PASS_SIX_FRESH_ORBSTACK_MODEL_HANDLE_EFFECT_SCOPED`. This is a six-allocation model-to-effect and fail-closed guard result. It is not a claim that the preregistered golden six-task comparison, baseline, human tempo, general reliability, or token efficiency has been reproduced.
- U: wire the complete model submit/revalidation method and the preregistered cold/warm/invalidation/repair workload, then compare against the frozen golden baseline without replacing prior evidence.

## OrbStack provenance

- Docker context: `orbstack`
- Docker image: `agent-interface-2558-orbstack@sha256:1a16aa431254514de58c909e84e5094a8e894caac11bf4c9d937dde6ea6d6398`
- Docker Server: 29.4.0
- Architecture: linux/aarch64
- OrbStack: 2.2.3
- Six fresh private Xvfb/fixture processes; no reused fixture state.

## Aggregate evidence

- summary SHA256: `95b07b429b95ffff5e175f3d652a8ac251b1004c95615d4fffeba80b9e401901`
- task evaluation hashes: `819571e42242bb3ed05c8a7dd6c6b9f04f75d28bf8a72524f3d2d1a6d6af4f35`, `6a9b9209d535d210e208da827c970b5540fd9eaba396a5815811f764e23a0530`, `d7b054d8a13950950b13e0b5ff353082f56c33b5a145c5c3a6a8837cce5b7d83`, `9f551bd9962579cbdbf53b09efb3a0d9a3aa1d99f6afd5080adf9466677f234a`, `af8cba7c0bb0ec8876d1292bf93d3b73534750d541cebbc9a88e7dfc2e3c37fa`, `c3e1d1abb8c520fae8fa9b02a6cd86b70ba3254d384b6f279c1d2c51b9ef56a5`
- all six guard reports had the same deterministic hash `cb3eaa9f3cb0c590102964a1ae9418ef2371c947502f574d2c7c22511a3677e5`

The earlier harness directory-exists stop and all previous #2558 results remain immutable.