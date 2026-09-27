# Issue #5045 — cross-process Needle publication

## Allocation and lineage

- Issue: #5045.
- Branch: `research/needle-cross-process-publication-5045-v1-20260928`.
- Path: `research/system1/needle_cross_process_publication_5045_v1/`.
- Base main at branch creation: `2b4891d99e3b938d1595d75ec978eb2e4ce6f5bf`.
- Exact immutable package input: #3890 seed-3788 `skill.json`, Git blob `45b80150dac503f4eb6f3cb5d82f9afa2c587107`.

#3890 already demonstrated static serialization and reload in separate processes. #4986 tested atomic replacement under threads. #4840 tested proposal metadata generation rules in a fixture. This allocation tests only their intersection that remains unmeasured: independent processes observing a live publication boundary and applying the generation fence to observations acquired on either side of it.

## H / T / D / C / U

**H.** When validation completes before same-directory `os.replace`, four independent reader processes observe only complete old/new package bytes; a deliberately synchronized in-place diagnostic exposes partial bytes; a candidate failing its content digest leaves ACTIVE byte-identical; and a proposal tied to the retired generation is refused after the switch.

**T.** Stage 0 is construction-only (syntax, exact schedule, four child PIDs distinct from publisher, reader IPC, and auditor mutation regressions); it must not run a formal publication schedule. Stage 1 uses one publisher and four fresh independent reader processes per arm (eight reader lifetimes total), explicit phase IPC (not sleep-only races), two arms (validated atomic replacement and partial in-place diagnostic), and fixed phases: old-before-validation, candidate-written-but-unpublished, boundary, post-switch, partial-diagnostic, completed-diagnostic, and invalid-candidate refusal. Each process reads/hashes bytes independently and records PID, request/phase ID, parsed generation/digest or parse failure. Proposals are synthetic shadow records only; no dispatch/authority.

**D.** Scoped PASS requires complete denominator, all atomic-arm reads matching complete old before switch and complete new after switch, no candidate observation before publication, at least one independent partial-read observation in diagnostic arm, exact ACTIVE hash preservation on invalid candidate, stale pre-switch proposal YIELD after switch and current-generation proposal ELIGIBLE_PROPOSAL_ONLY, zero dispatch, all process exits 0, independent raw-only audit with zero errors, and every frozen corruption control rejected. Any failure of a fully observed semantic gate is FAIL; provenance/resource/audit/evidence gaps are typed STOP/HOLD. No retry or post-result threshold changes.

**C.** One Docker Desktop Linux/amd64 engine, Python multiprocessing and its mounted filesystem/overlay. IPC barriers force only a finite schedule; results do not estimate race probabilities. Atomic rename semantics may differ on other filesystems. This cannot demonstrate crash durability or power-loss behavior.

**U.** Inert synthetic JSON only. No training, inference, Astra feedback, real-time LoRA, intent routing, GUI/task effects, cross-host semantics, production authority/safety, deployment or latency claim.

## Freeze / execution gates

- Image: cached `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64; network none, pull never, read-only root/source, 0.25 CPU, 256 MiB, 32 PIDs, fresh writable output.
- Package bytes and Git blob above are read-only references; no predecessor files edited.
- Freeze exact runner/auditor/test/image/command hashes, phase roster and empty output before any formal container launch.
- Formal Docker lease is not inferred from momentary utilization. Obtain explicit coordination from other active lanes, then freshly inspect Docker immediately before the one formal invocation. Do not stop/modify existing containers.
- If no exclusive/shared lease is granted, record a pre-run `STOP_RESOURCE_OR_OWNERSHIP_UNCLEAR` in a separate evidence artifact; do not label it scientific evidence and do not launch.




## Successor correction

This v2 allocation was created after #5045's immutable pre-formal STOP. The v1 host orchestrator read a nonexistent top-level `input_sha256`, while the registered freeze used `input.sha256`. This version adds `--preflight-only`, verifies the nested frozen digest, and has integration regressions that exercise the registered freeze with zero Docker invocations and assert the output path remains absent. The v1 sources/freeze/STOPs remain unchanged.
