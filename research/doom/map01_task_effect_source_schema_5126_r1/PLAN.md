# MAP01 task-effect source-schema audit, r1

## H/T/D/C/U

- **H — Hypothesis:** the current-main v13 composition does not publish an immutable identity shared across its physical-input and independent-scorer evidence. The synthetic `source_event_id` fields in the older task-effect contract are test inputs, not fields shown to be emitted by these producers. If the physical input identity and scorer epoch cannot be reconstructed from producer output, task-effect attribution must remain on HOLD.
- **T — Test:** statically inspect the pinned producer code on main `e8b4071931df81b3408a5d0a91c7607c6323c9c9`. Record exact producer wire keys for v13 release telemetry and scorer events, distinguish the retained v12 physical-edge implementation from the current v13 input path, and check whether a stable source-event identity is emitted. Freeze Git blob IDs and SHA-256 hashes before evaluation.
- **D — Decision:** `HOLD_SOURCE_IDENTITY_INSUFFICIENT` if current v13 producer outputs contain no per-event source ID and no common physical/scorer epoch key; report only source-schema availability, not a runtime collision or end-to-end lineage failure.
- **C — Controls:** host-only static source inspection; no GUI, DOOM, X11, OS input, model, GPU, Docker, network, or changes to prior PR/issue artifacts. No experiment result is inferred from the synthetic cases in contract #1839.
- **U — Uncertainty:** source inspection establishes declared/constructed fields in pinned code, not the exact contents of a future live run or downstream serialization performed outside the inspected functions.

## Scope boundaries

The current v13 composition substitutes `doom_retained_input_backend_v3` and `input_transition_owner_v3` over retained `session_map01_v12`. The v3 transition wrapper returns release receipts; v3 backend emits these after a batch owner-state sample. The independent scorer clock emits scorer events on a separate sink. The older physical down/up bracket and adapter (`map01_attack_onset_phase_allocation_04_v1/dependencies/v12`) are inspected only to establish whether their internal edge IDs survive its typed adapter boundary; they are not asserted to be the v13 active runtime path.

The audit will write a machine-readable result and independent verification output next to this plan. It will not claim a task-effect PASS, establish observed runtime collisions, or modify #5126/#5131/#5132/#1839 artifacts.
