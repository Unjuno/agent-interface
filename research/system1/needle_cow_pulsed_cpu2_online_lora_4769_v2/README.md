# Query-pulsed CPU2 COW Needle LoRA successor (#4917)

This path reserves an experiment against #4917. The Stage-0 passes below are construction evidence only; no optimizer update or formal cell has run, and no PR/main integration is implied.

## Intake and lineage

- Parent: #4769, completed CPU-quota comparison, retained as `HOLD_NO_CONCURRENCY_PRESSURE`.
- Schedule-only surrogate: PR #4915, construction-only; it tests integer/event schedule cardinality and publication boundaries, not model state, COW behavior, actual query overlap, or latency.
- Current main at intake: `f3dc0f18b0aaef241a6cd34124b68439c3434b05`; re-read main immediately before formal freeze.
- Candidate formal allocation/seeds and H/T/D/C/U: see Issue #4917. Current proposal: 91004321/91004531/91004749, not yet frozen or consumed.
- Candidate pinned image: `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64; inspected locally as exact image ID/platform.

## Resource and ownership gate

At intake, shared Docker had two sibling containers (`cranky_panini` X11 diagnostic and `agent-interface-570-r3-ollama`); they remain untouched. A separate sibling had run the PR #4915 CPU construction surrogate. Do not start formal Docker work until all relevant task owners explicitly clear shared CPU use and a fresh container/resource check passes. Never stop, reconfigure, or enter sibling containers. If ownership cannot be verified, preserve a typed STOP before formal seed use.

## Stage 0 construction record (zero optimizer steps)

- Stage0-01: STOP, 9/10 tests passed, exit 1; required `NEEDLE_EXPECTED_CPUS` omitted. Stdout SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; stderr SHA-256 `34f80163e457138ad20d8bfa19fd2f372cfaf319adde37a48dbe8512936f182e`.
- Stage0-02: corrected invocation with `--cpus=2` and `NEEDLE_EXPECTED_CPUS=2`; 10/10 tests passed, exit 0. Stdout SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; stderr SHA-256 `ab3f9cde9e5c56dd02a9e30cdbc72d1fa8162b884ffc8782457128d068ac5060`. This tested the then-proposed seed block, before the collision-driven replacement.
- Stage0-03: final proposed seed block 91004321/91004531/91004749; same corrected quota/env; 10/10 tests passed in 0.029s, exit 0. Stdout SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; stderr SHA-256 `5802a4a3a8e4ca6072fe81fe8256ffd975c5cf16d3b09c23bf593c904001c904`. Docker source was mounted read-only, network disabled, CPU quota 2; no model fitting or formal seed consumption. PyTorch emitted a non-fatal warning that NumPy was unavailable. Raw logs remain under local `scratch/needle-4917-v2-container/stage0-01..03/`.

The earlier proposal seed 9767203 appeared as a substring in an unrelated archived Doom `image_ready_ns` timestamp, and 9767219 in unrelated live-control timestamps; both were retired without use. Exact searches before uploading this candidate source returned zero hits for 91004321/91004531/91004749 across issues, PRs, branches, commits and main code. The runner uses direct per-seed `torch.Generator.manual_seed(seed)`, with no derived RNG offsets. Final freeze still requires exact live collision and source readback records.

## Required next gates

1. Re-read current main and all four frozen source blobs; verify exact bytes/hashes and collision searches immediately before freeze.
2. Freeze runner, independent auditor, tests, commands, environment/image identities, allocation and report gates before any formal cell.
3. After explicit CPU ownership clearance and fresh resource check, run six paired fresh-seed continuous/pulsed cells exactly once in Docker and independent raw-only auditor exactly once in a separate container. No retry, tuning, fallback, seed substitution or runtime promotion.
4. Record raw rows/logs/invocations/audit/limitations on #4917 and deliver through a reviewable PR. Merge only when evidence, CI and review gates permit.

All source/result files added here are additive. Preserve #4653/#4769/#4915 artifacts and outcomes unchanged.
