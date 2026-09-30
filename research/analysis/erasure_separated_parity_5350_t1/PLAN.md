# Erasure-separated parity and authority boundary T1

Allocation: `erasure-separated-parity-5350-t1-20260930-01`
Issue: [#5350](https://github.com/Unjuno/agent-interface/issues/5350)
Registration/frozen main: `e81cbac968752791678d22a4de3f2d276497d614`
Branch: `research/erasure-separated-parity-5350-t1-20260930`
Path: `research/analysis/erasure_separated_parity_5350_t1/`

## H/T/D/C/U

**H.** Two disjoint XOR parity groups can recover one missing symbol per group for presentation independent of arrival order, while reconstructed critical content, incomplete exact sources, or invalid provenance never qualify as authority.

**T.** Four source bytes in groups `(a,b)` and `(c,d)`, one parity byte per pair. Nine cases cover complete/reordered delivery, single loss, cross-group double loss, same-group double loss, parity loss, mixed generation, and criticality metadata mismatch. Each shard records arrival order/tick, generation, and criticality.

**D.** PASS_SCOPED iff exact reconstruction and availability match the literal oracle; same-group two-erasure fails; cross-group one-per-group recovers presentation; any reconstruction is non-authoritative; authority requires all exact original source chunks and valid single-generation/criticality metadata; mixed/mismatched metadata rejects; independent audit passes.

**C.** Host-only exact-byte XOR toy, Python 3.14.5 / Darwin arm64 / stdlib. No Docker/OrbStack CLI under current coordinator hold. Runner and raw-only auditor each once; no retry.

**U.** No fountain-code/rateless result, real transport timing, measured latency/bandwidth, reliable criticality classifier, GUI safety, or production claim. Tick values encode ordering only, not wall-clock delay.
