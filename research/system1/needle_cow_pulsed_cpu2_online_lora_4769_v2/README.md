# Query-pulsed CPU2 COW Needle LoRA successor (#4917)

This path reserves an experiment against #4917. It is not a result. No source is frozen, no optimizer update or formal cell has run, and no PR/main integration is implied.

## Intake and lineage

- Parent: #4769, completed CPU-quota comparison, retained as `HOLD_NO_CONCURRENCY_PRESSURE`.
- Schedule-only surrogate: PR #4915, construction-only; it tests integer/event schedule cardinality and publication boundaries, not model state, COW behavior, actual query overlap, or latency.
- Current main at intake: `f3dc0f18b0aaef241a6cd34124b68439c3434b05`.
- Candidate formal allocation/seeds and H/T/D/C/U: see Issue #4917. Seeds remain proposals until exact source/RNG-offset/collision audit and freeze.
- Candidate pinned image: `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64. Reinspect ID and platform immediately before any use.

## Resource and ownership gate

At the latest check, shared Docker had two sibling containers (`cranky_panini` X11 diagnostic and `agent-interface-570-r3-ollama`) and a separate sibling had just run the PR #4915 CPU construction surrogate. They were left untouched. Do not start Docker work until all relevant task owners explicitly clear shared CPU use and a fresh container/resource check passes. Do not stop, reconfigure, or enter any sibling container. If ownership cannot be verified, preserve a typed STOP before formal seed use.

## Required order

1. Perform full issue/branch/PR/commit/seed derivation and exact-main source readback. Incorporate the independently reviewed PR #4915 schedule-only construction evidence only as a design input.
2. Implement and run an isolated, zero-optimizer-step construction suite. Keep output/log/raw/audit directories separate and empty as required. Construction success must not be called a model or latency result.
3. Freeze runner, independent auditor, tests, commands, environment/image identities, and report gates. Read back each frozen Git blob and hash before any formal run.
4. Only after explicit CPU ownership clearance, run the six paired fresh-seed continuous/pulsed cells exactly once in Docker and the independent auditor exactly once in a separate container. No retry, tuning, fallback, seed substitution or runtime promotion.
5. Record all raw rows/logs/invocations/audit/limitations, report outcome on #4917, and deliver through a reviewable PR. Merge only when evidence, CI and review gates permit.

All source/result files added here must be additive. Preserve #4653/#4769/#4915 artifacts and outcomes unchanged.