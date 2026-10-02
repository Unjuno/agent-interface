# Freeze-only archival qualification — Issue #4063

Exact `FREEZE.json` from `research/outcome-poll-snapshot-d19a-20260922` at `de1855f5b976a4d4a8ee84b8bdd4fcd4d22a11f9`; source Git blob `4f5a046ed8474ad6666bed9ccc1f647dcc29567d` is preserved unchanged.

- **H:** retain the 24-case allocation identity and source hashes to prevent accidental duplicate execution.
- **T:** the remote branch contained only this freeze. Issue #4063 reports a 24-case scoped PASS, but exact source/raw/audit bytes are absent from the branch and main; the distinct PR #4102 allocation is not a substitute. No associated workflow artifact was found; no formal rerun was performed.
- **D:** `HOLD_SOURCE_AND_RAW_UNAVAILABLE`; metadata preservation only, not independent reproduction or result promotion.
- **C:** a related allocation cannot be pooled or substituted for this one.
- **U:** repository-restorable source/raw and an independent audit remain absent. Issue #4063 remains open.

Original branch history is archived at `archive/recovered/outcome-poll-snapshot-4063-20260922`.
