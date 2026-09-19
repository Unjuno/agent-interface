# Excluded construction

Formal measured rows at freeze: **0**.

Construction is excluded from the formal denominator and establishes only mechanism/harness viability.

1. Exact promoted `runtime/core_v1/contract.py` was reconstructed from immutable BASE and verified as Git blob `a16620b65d22757ca9160d68feb1381306cc6ac3`, SHA-256 `268cf282c02f9e2dd38a8c45a36378049443ef2a2431063359011d0552b9c37c`, 13,869 bytes.
2. First dynamic-import attempt exposed only a Python 3.13 loader defect: the module was not inserted in `sys.modules` before `exec_module`, so `dataclass` could not resolve its module namespace. Loader-only repair; core bytes and bridge semantics unchanged.
3. Excluded construction exposed the intended discriminator: `naive_bridge` can retain a HISTORICAL HINT target point while substituting current numeric source fields, and promoted core admits the resulting ordinary program; `typed_bridge` refuses that weak lineage before program construction. Exact explicit current revalidation remains live.
4. A deterministic 22-row construction-shape run plus auditor passed before source freeze. Those rows are not formal evidence and are not pooled.
