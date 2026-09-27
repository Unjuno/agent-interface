# Allocation-02 construction / provenance

No new scientific GUI construction was run for allocation-02 because the only changed factor is the external outer orchestration granularity; `study.py`, `execute.py`, `audit.py`, `controls.py`, `test_contract.py` and environment are copied byte-for-byte from allocation-01.

Allocation-01 excluded construction remains canonical under Issue #4424: initial `XVFB_NOT_READY` setup STOPs, then the setup-only propagation repair and three complete disjoint `(8,5)` cells. Those rows remain excluded from both formal denominators.

Allocation-01 formal STOP is immutable and not construction: cases0-4 complete, case5 incomplete under external execution-surface timeout, cases6-11 unstarted. None are pooled into allocation-02.

Before allocation-02 freeze, the unchanged pure contract suite is run from this directory and must pass 3/3. Formal remains 0 until exact v2 source/gate GitHub readback.
