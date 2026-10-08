# Real-GUI temporal ring experiment — Issue #2947

Status: **pre-formal source/gate freeze only**. Formal allocation count: 0.

This additive path owns the prospective allocation `temporal-ring-real-gui-2947-a91f-20260922-01`.
It preserves #2013/#1029 and all predecessor evidence unchanged.

The exact frozen local source, PLAN, environment, construction record, tests, auditor,
two-batch wrapper and corruption controls are stored losslessly in the source capsule:

- archive bytes: 14,588
- archive SHA-256: `7cf051f5d90552fee2a6f46e08cbcc07cd8474880ec5ef3ba3f87b9a283651e2`
- parts: `SOURCE.part00.b64`, `SOURCE.part01.b64`
- frozen source manifest: `FREEZE.json`
- restore with: `python -I -S -B restore_source.py /tmp/a2947-source`

Formal design after excluded construction: 11 scenarios x 2 fresh repetitions = 22
private-Xvfb/Tk source cases and 44 matched read-only policy cells. Two immutable
11-case batches are preregistered. TEMPORAL_RING must be 22/22 independently
correct with zero role/scope laundering and CURRENT_ONLY must expose the six
frozen transient-history misses. Ten copied-evidence corruptions must reject.

Frozen support budget: XGetImage p95 <=10ms; non-SESSION_REPLACE schedule lateness
max <=30ms; query p95 <=1ms; inspector subprocess wall p95 <=100ms; response
<=65,536 bytes; raw frame bytes per source case <=40,960. No input/action authority,
model/provider/network/user desktop, product or global-roadmap claim.

Construction and all exact H/T/D/C/U details are in the capsule PLAN.md and
CONSTRUCTION.md. Construction rows are excluded from formal denominators.
