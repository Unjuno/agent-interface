# Issue #5024 — exact-base reproduction procedure addendum

A preliminary checkout attempt exposed an ordering flaw before the frozen-base gate: the partial clone's checkout started at origin/main `ba546e7a91874bb1476262957954679bdd1c932a`, then `git checkout --detach 30793b0fcc05bb7d27c4bc1cae2aaf588321262b` returned 1 on the literal-backslash paths before moving HEAD. Readback confirmed HEAD remained `ba546e7a91874bb1476262957954679bdd1c932a`. Preserve this as `STOP_BASE_NOT_REACHED`; do not count it as the preregistered frozen-base result.

Before the single counted baseline reproduction, use a fresh clone and stage sparsity so the exact base can be selected without materializing the offending subtree:

1. Clone main with `--filter=blob:none --no-checkout --single-branch --branch main`.
2. Initialize cone-mode sparse checkout and set it to `docs` only.
3. Checkout detached frozen base `30793b0fcc05bb7d27c4bc1cae2aaf588321262b`; assert `rev-parse HEAD` equals that SHA.
4. Add the complete `research/analysis/gpu_grounding_template_diversity_2912_v2/results/formal01` subtree to the sparse set. Capture this command's exit/stderr and enumerate all invalid-path diagnostics. This is the counted clean Windows checkout reproduction.

The baseline remains untouched after the failure. Repair validation uses another fresh clone; checkout the same frozen base while excluding the affected subtree, then fetch/check out the repair commit and add the same subtree. This addendum was written before the corrected attempt; it does not revise the frozen tree, target mapping, hypothesis, or gates.
