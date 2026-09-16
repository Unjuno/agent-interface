# Excluded construction

Formal measured rows at freeze: **0**.

Construction is excluded from the formal denominator.

1. Exact BASE `runtime/cli_v1/api.py` was reconstructed and verified as Git blob `58e5489796959f120d973b595f36ed3d808533b3`, 2,162 bytes.
2. Exact promoted `runtime/core_v1/contract.py` was reused and verified as Git blob `a16620b65d22757ca9160d68feb1381306cc6ac3`, 13,869 bytes.
3. Fake `runtime.selector_v1` only replaces backend opening and counts `open_session` / `session.dispatch`; fake session delegates admission to exact core-v1.
4. One deterministic 22-row construction-shaped matrix and auditor PASS before freeze. Construction is not pooled.
