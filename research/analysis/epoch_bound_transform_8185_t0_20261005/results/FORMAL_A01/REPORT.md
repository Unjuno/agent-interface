# Issue #8185 T0 A01 result

**Disposition: PASS_METHOD_SCOPED (method-scoped).**

The frozen synthetic audit covered 19 cases: 3 direct baseline controls, 3 exact-safe composed cases, 2 uncertainty controls, and 9 invalid-chain/binding/model controls. The independent auditor found **0 false admissions**. All **9/9 invalid controls** failed closed. For the 3 exact-safe composed cases, the graph admitted 3/3 while the direct-map baseline abstained on 3/3, a **100% reduction in false UNKNOWNs** in this finite corpus. Independent measurement-error control abstained in both methods.

This is a deterministic finite-model result only. It supports the hypothesis that explicit, typed chain composition can recover valid composed affine mappings missed by a single direct map under these fixtures. It does not establish native mixed-DPI behavior, actual epoch/race correctness, GUI or OS input behavior, arbitrary transforms, latency, or task effect. T1 remains unrun and separately gated.

The candidate and auditor each ran once in the pinned `linux/arm64` Python 3.12.15 OrbStack container with network disabled, one CPU, 512 MiB memory, and read-only root. Construction tests were separate pre-freeze checks and are not part of the formal result.

Allocation: `UNJUNO-8185-TRANSFORM-T0-A01-20261005-01`. Freeze receipt: SHA-256 `82ada9c98b435991abdeea3b77c88f9e1a59f78461d9383b0a16a97c081db1d7`. Candidate output: `55cea9d2a1efd2d6af32a4bbe6828412556c17422820dda6249bba42ba4605d6`. Audit: `bec1e04a8b65519b880bec69431db7d71b706c474867c75ba8a2392c76c036d5`.
