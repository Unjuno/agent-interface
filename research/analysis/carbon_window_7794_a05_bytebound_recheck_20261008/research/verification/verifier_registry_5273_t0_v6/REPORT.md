# Issue #5273 — T0 v6 complete-registry preflight

**Disposition: PASS_HOST_CONSTRUCTION_ONLY; formal container gate STOP.**

This is a review-driven, additive successor. It preserves v1-v5 and does not modify the #5268 IR or neighboring roadmap work. GitHub Issue #5273 remains open; this package does not complete the heterogeneous registry qualification.

## H / T / D / C / U

- **H:** An explicit verifier descriptor and exact assignment-to-IR-check coverage allow deterministic preflight to reject unsupported evidence, stale versions, prohibited effects, unavailable resources, budget violations, and infeasible deadlines before any dispatch.
- **T:** Frozen eight-case corpus includes all Issue #5273 acceptance cases: unsupported primitive, wrong evidence role, stale verifier version, unavailable resource, cold-only budget violation, warm feasible route, prohibited verifier side effect, and deadline infeasible with unavailable resources. Construction tests additionally exercise output-role mismatch, unknown and duplicate verifier IDs, duplicate/missing/extra assignment coverage, null deadline, and the five heterogeneous descriptor categories.
- **D:** **21/21 host tests pass.** Eight raw outcomes agree with a separate oracle (8/8); raw auditor reports PASS; corruption tests reject changed decisions, input binding, extra fields, and falsely measured cost. All routes report zero dispatch and authority NONE. Result is scoped to synthetic fixture preflight only.
- **C:** Main was refreshed before freeze to 1f858cf0d2da2821b5767077e1c9556764507dbb. Corpus SHA-256: 82388580fcaff7e4d6ebe55a8ea40d21fbe28cc51c422f1064c2bcabd81ccfaf. Raw SHA-256: b293715ee83c18962f49fe4c5278e84e86a956e470d7a1124d7a9835acb19eee. See FREEZE.json for source hashes. All costs and latency/tick bounds are synthetic declared estimates, not measured facts. Shared #5085 coordination has no exact lease for this package and reports active competing requests; therefore the container gate is **STOP_NO_EXACT_RESOURCE_LEASE**, with zero invocations and zero Docker/OrbStack commands.
- **U:** This does not establish verifier correctness, real latency/cost, scheduler speedup, dependency ordering, runtime integration, resource availability on any machine, model/GPU/container behavior, or action authority.

## Preserved construction failures and boundaries

The first expanded test pass exposed five missing behaviors: check/assignment coverage, cold budget rejection, deadline precedence, prohibited side-effect rejection, and explicit unavailable-resource classification. Those failures preceded the corresponding implementation. A separate duplicate-descriptor probe caught first-match ambiguity and is now rejected. The output-category retention test also first failed because the raw decision omitted that metadata; the field is now emitted and independently checked. These were construction findings, not formal verifier runs.

The v4 boundary disagreement and prior v1-v5 review findings remain in their original PRs and evidence. This successor specifically tests the combined acceptance surface but remains a host-only construction artifact. Do not promote it to a container or operational result.

## Reproduction

Follow README.md from this directory. cases.json and raw_host.json are frozen evidence; do not regenerate them. To independently rerun the host construction after inspecting hashes, use a copy or a new successor version.
