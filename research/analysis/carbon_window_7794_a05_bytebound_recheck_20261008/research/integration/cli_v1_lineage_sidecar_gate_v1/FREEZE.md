# PRE-MEASUREMENT FREEZE

Task `CLI-V1-LINEAGE-SIDECAR-GATE-20260917-001`, Issue #787.

Immutable publication BASE: `1a529d2b593eb246846cfa14f27ec7617b7fe966`.
Owned additive scope: `research/integration/cli_v1_lineage_sidecar_gate_v1/**` only.

Formal measured rows at freeze: **0**.
Formal runner invocation budget: **1**. Same-allocation rerun/replacement budget: **0**.

Pinned exact dependencies:
- `runtime/cli_v1/api.py`: Git blob `58e5489796959f120d973b595f36ed3d808533b3`, SHA-256 `1369a408438a013dbca5b891863c0b834f338e657f0937a291064d089eb92900`, 2,162 bytes.
- `runtime/core_v1/contract.py`: Git blob `a16620b65d22757ca9160d68feb1381306cc6ac3`, SHA-256 `268cf282c02f9e2dd38a8c45a36378049443ef2a2431063359011d0552b9c37c`, 13,869 bytes.

Single factor: raw exact CLI dispatch versus content-bound lineage sidecar gate before exact CLI dispatch. CLI/core bytes are unchanged.

Prefreeze `py_compile` PASS; deterministic static tests **4/4 PASS**. Excluded construction is retained separately and not pooled.
