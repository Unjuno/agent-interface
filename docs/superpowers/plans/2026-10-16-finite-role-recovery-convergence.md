# Finite role recovery convergence plan

**Goal:** Preserve PR7264/8370 recovery ideas on current main and distinguish bounded synthetic recovery from application-qualified recovery.

**Sources:** PR7264 `8fe7c2b7a955187939014aff33cf61ed01ea90e9`; PR8370 `9fb4a64d6a86fc2eb01b4e984508e8f320bb3e31`; base `d6121c641ac1e56377e0ebb4bff6fb88d2d66833`.

**Architecture:** Adopt the byte-identical package and portable tests. Preserve all nine original changed files from each PR, including different parent README contexts, as inert data. Run public-state tests and file-backed fixture cells in retention/replan modes; independently read raw saved files against literal expected effects. No automatic caller integration.

**Constraints:** Local synthetic subject/editor only. No GUI/native input/model/provider/WSL/container or consumed experiment replay. Fixture Save is not application certification. Historical quorum/allocation records are data, not current approval requirements.

- [ ] Preserve original files/head snapshots; adopt without behavior edits.
- [ ] Run 26 original tests normal/-O; ten file-backed cells per mode: stable, annotation change, role invalidation, second change, unknown replacement, each retention/replan. Retain counters and exact bytes; saved-only audit rejects contradictory copies.
- [ ] Publish conditions/source/raw/readback/limitations; review immutable patch.
- [ ] Integrate and verify merged state, close converged originals with continuation, remove own safe temporary refs.

**Unqualified:** selected target/generation and standard v3/guarded adapter; native release/cancel bounds; application Save/disk truth; semantic role oracle; concurrent outside-writer atomicity; provider economics. Direct pipeline request custody is outside wrapper qualification.
