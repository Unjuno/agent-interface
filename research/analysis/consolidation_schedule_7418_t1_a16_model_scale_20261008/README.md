# T1-A16 model-scale comparison

A16 tests a competing explanation for the repeated transition-audit failures: the 8B model may not reliably follow the fixed structured consolidation contract. Relative to A15, only model scale changes, from Qwen3 8B to Qwen3 14B. Both are Q4_K_M variants with the same Qwen3 family and prompt, schema, fixture, schedule, query set, decoder settings, and independent auditor. Fresh seeds are 5601, 5602, and 5603; no outputs are pooled.

Posthoc raw-only analysis found that the frozen effect-claim mapping omits applicability context and that the auditor does not validate it. This narrows the meaning of A16's `PASS_METHOD`; see `results/FORMAL_T1_A16/APPLICABILITY_SCOPE_DIAGNOSTIC.md`.

The 14B model tag is pinned by digest `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`. The independent preflight checks the tag and every manifest layer in the dedicated private store. The allocation is 390 calls, with the same STOP and interpretation gates as A15; see `PROTOCOL.md`.
