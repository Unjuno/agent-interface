# Freeze-only archival qualification — Issue #4061

Exact `FREEZE.json` from `research/text-consumption-context-9bd1-20260922` at `a159a9c7a9181d5f4219db49c55f2ad7d046b527`; source Git blob `ab421a7d0286d3cdc10fb626fe376d06ebecbab7` is preserved unchanged.

- **H:** retain the 28-case allocation identity and declared file hashes to prevent accidental duplicate execution.
- **T:** the remote branch contained only this freeze. Issue #4061 reports a 28/28 scoped PASS and identifies a 264-file/13,027,724-byte capsule (SHA-256 `de96472d4d0a3b7ca74c35b01c619210c8c4970f6416a5021b4eb6a526bbc045`), but that capsule is not retrievable from the branch, Actions artifacts, or bounded local searches. No formal rerun was performed.
- **D:** `HOLD_SOURCE_AND_RAW_UNAVAILABLE`; metadata preservation only, not independent reproduction or result promotion.
- **C:** an issue-reported capsule hash does not make its bytes available for repository-only audit.
- **U:** exact source/raw capsule and independent audit remain unavailable. Issue #4061 remains open.

Original branch history is archived at `archive/recovered/text-consumption-context-4061-20260922`.
