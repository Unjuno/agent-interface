# WSL 3.x Dockerless migration: residual workflow inventory

Date: 2026-10-12
Audit base: `main` at `f185a9059d485a4f8d5a65e9e7f6782897f67eae`
Scope: read-only documentation/workflow classification. No containers, images, Docker daemon, WSL configuration, formal allocation, or runtime were changed or launched for this inventory.

## Decision

The repository has already migrated its default eligible local iteration route: use native Ubuntu/WSL when no image boundary is needed, and WSLc for a single-container/image workflow when its required features are supported. Docker is not a general prerequisite. This inventory does **not** recommend blanket replacement of every historical Docker command. A frozen command that encodes Docker-specific controls or a Docker Engine/Compose dependency is not semantically interchangeable merely because WSLc can launch a container.

No latency, memory, OOM, hard-cap, security-equivalence, or universal compatibility improvement is inferred. Main's current migration policy and prior bounded execution records remain authoritative; this note only identifies residual documented examples.

## Route classification

| Tracked path | Current role | Migration disposition |
|---|---|---|
| `.github/wslc-local-containers.md` | WSL/native versus WSLc route selection, supported-control caveats and promotion policy | Keep as the operational policy. It already removes Docker as a default for eligible local single-container work and preserves hosted CI. |
| `.github/scripts/test_wslc_local_runtime.ps1` | Unique-scope, pinned-image WSLc smoke and cleanup verification | Keep as the narrow compatibility check. Do not repeat it absent a new question; an accepted memory request is not proof of enforcement. |
| `runtime/WSL_NATIVE.md`, `runtime/integration_checks/README.md`, `runtime/integration_checks/wsl-native.ps1` | Native WSL fast iteration and Windows launcher for existing contract checks | Keep native WSL as the default when no container boundary is required. Reuse the provisioned environment and fresh result paths. |
| `runtime/integration_checks/README.md` “Optional legacy Docker environment matching” | Reproducible local route for the fixed native contract suite | Retain as explicitly optional compatibility guidance. The default suite already has a Dockerless native route; hosted CI is separate. A WSLc version is not added here because the suite's equivalent controls and environment are not newly re-qualified by this static audit. |
| `research/live_control/native_mcp_container/README.md` | Private X11/MCP harness with frozen Docker-oriented invocation, private Xvfb, retained failed-run evidence and explicit lifecycle | Preserve for the existing protocol. A replacement needs a separate compatibility qualification of image/build inputs, stdio behavior, Xvfb, writable evidence mount and failure custody; this inventory does not establish equivalence. |
| `research/procedural_ops_facility_v0/README.md` | Native C/X11 benchmark with headless and Xvfb paths; optional container build/test recipe | Prefer native `make`/tests for eligible local iteration. Keep container recipe as optional. Any WSLc recipe must first verify its X11/Xvfb dependencies and exact fresh-output behavior. No such run was made here. |
| `research/experiments/procedural_arena_v1_recovery_boundary_4695_v1/README.md` | Reproduction commands explicitly request Docker `--read-only`, dropped capabilities, no-new-privileges, resource bounds, and network isolation | Preserve frozen historical command. The current WSLc policy does not establish equivalent rootfs/capability/security controls or hard memory enforcement; rewriting would change the protocol without a separately authorized qualification. |
| `RUN_PROTOCOL.md` and frozen Docker allocation records | One-shot candidate/environment/auditor stages with Docker-specific read-only root, capability, PID, network, mount, and image controls | Preserve immutable allocation instructions and results. Do not replay or relabel them as WSLc. New experiments need a distinct preregistration and runtime-eligibility gate. |
| `.github/workflows/**` | Hosted shared CI | Out of scope for local-runtime migration. Keep hosted CI unchanged. |

## H / T / D / C / U

- **H:** Applying the already-established native-WSL/WSLc policy to new eligible local work removes Docker as a prerequisite without changing the experiment. Residual Docker references that encode frozen protocol controls should remain until separately qualified replacements exist. This predicts no performance or memory improvement.
- **T:** For any future candidate path, first verify current-main source and ownership; classify the exact required boundary and controls; choose native WSL if no container is needed, otherwise WSLc only when every required control is documented and evidenced. Make only additive documentation or workflow changes, preserve old commands/results, and validate new instructions without consuming a prior allocation.
- **D:** Migration is complete for the default-route policy when eligible local workflows no longer require Docker by assumption and documented exceptions are explicit. A particular Docker recipe may be replaced only after a separately scoped compatibility review establishes the required behavior and evidence custody. Any performance/memory claim requires its own matched study.
- **C:** Native WSL may not satisfy reproducibility/isolation needs; WSLc is not Docker Engine/Compose-compatible and lacks some Docker controls; leaving optional Docker recipes can confuse readers if their optional/historical scope is not clear.
- **U:** This is a static bounded search, not an exhaustive proof that every tracked Docker invocation was found. It does not verify runtime behavior, effective resource limits, security boundaries, dependency parity, or the current shared WSLc owner/readiness state.

## Related records

- [#8619 — WSLc GA migration policy and current Dockerless readiness](https://github.com/Unjuno/agent-interface/issues/8619)
- [#8677 — Dockerless migration continuation and lane gate](https://github.com/Unjuno/agent-interface/issues/8677)
- [#8882 — residual Docker-first documentation inventory](https://github.com/Unjuno/agent-interface/issues/8882)
- [#7428 — eligible local WSLc default migration](https://github.com/Unjuno/agent-interface/pull/7428)
- [#8133 — WSL 3 Dockerless local iteration docs](https://github.com/Unjuno/agent-interface/pull/8133)
- [#8570 — native WSL or WSLc route selection docs](https://github.com/Unjuno/agent-interface/pull/8570)

## Evidence and stop boundary

This inventory read current-main `runtime/WSL_NATIVE.md`, `runtime/integration_checks/README.md`, the WSLc policy referenced by #8619, and targeted current-main Docker build/run code-search results. It did not execute a repository test or runtime probe. The supplied task directory is a research-copy collection rather than a Git checkout, so no local repository files were changed. No remote shared-runtime ownership release was obtained; therefore no WSLc launch, container/image inventory, cleanup, Docker operation, WSL restart, or memory-pressure test was performed.
