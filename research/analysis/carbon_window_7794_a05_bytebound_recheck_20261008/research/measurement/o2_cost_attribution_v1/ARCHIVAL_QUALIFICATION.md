# Freeze-only archival qualification — Issue #4065

Exact `FREEZE.json` from `research/o2-cost-attribution-20260922` at `da2a271f819fcdb487474964277911aad3bb9528`; source Git blob `de308430febbc80a2ced4f221fba405ea2c2e50b` is preserved unchanged.

- **H:** retain the CPU-attribution allocation identity and source/corpus hashes to prevent accidental duplicate execution.
- **T:** the remote branch contained only this freeze. Issue #4065 reports one allocation and `HOLD_ATTRIBUTION_NOT_ESTABLISHED`; the reported comparison-expression fraction median was 0.2403 against a <=0.15 gate. Exact source, corpus, formal raw and audit are unavailable; no formal rerun was performed.
- **D:** preserve the Issue-reported HOLD only; no overall PASS or performance claim is made.
- **C:** a failed attribution threshold is not evidence of a benefit, and the report alone is not a repository-only reproduction.
- **U:** exact source/corpus/raw and independent audit remain unavailable. Issue #4065 remains open.

Original branch history is archived at `archive/recovered/o2-cost-attribution-4065-20260922`.
