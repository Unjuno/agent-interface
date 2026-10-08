# Issue #5518 T7 — input-conditioned bounded quiescence deadline

## Disposition

**PASS for the preregistered six-trace finite-contract gate.** The candidate accepted the three declared-conforming traces and rejected the three forbidden traces. The independent auditor reconstructed all six from the raw I/O event sequences and matched every expected decision and first-forbidden-event index. Mutation controls rejected all three corruptions.

## Formal evidence

- Preregistration: Issue comment [#5913367240](https://github.com/Unjuno/agent-interface/issues/5518#issuecomment-5913367240), before allocation.
- Base HEAD: `ddd2a4b473f7418665619cdacff60cc2b306ad95`.
- Runtime: OrbStack Docker Linux/ARM64; `--network none --cpus=1 --memory=512m`; `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Frozen runner SHA-256: `1feef108a7c81adafa1bb00d55d093c7e9244a42b8a7a445cb2dc7b7f0e700b8`.
- Frozen independent auditor SHA-256: `f399ff846f9756601d0e3ea52e0b138486e1bc425d02236f91d4a0f1cd2f88b3`.
- Frozen mutation-controls SHA-256: `490a444e77c9ca0e132a92052bbf9cba5f5695afe8c2732bab3a2b4426ceeab8`.
- Raw JSONL SHA-256: `e100971e8342926ad7c8d64e6c58de72661bbf436ad256f066585734d8dee766` (`raw/formal/results.jsonl`).
- Independent audit: `{"audit":"PASS","decision":"PASS","errors":[],"independent_counts":{"conformant":3,"rejected":3}}`.
- Mutation-control result: 3/3 rejected; raw controls output SHA-256 `fcecd290bc322c5e900f8b7470ec3dadb88acf830c4e954fba6b2370f8faa258`.

| Trace | Result | First forbidden event |
|---|---|---:|
| OBSERVE, hidden TAU_RETRY, RECEIPT@1 | conformant | — |
| OBSERVE, QUIESCENT@2 | conformant at inclusive deadline | — |
| OBSERVE, QUIESCENT@3 | rejected | 1 |
| OBSERVE, UNKNOWN@3 | conformant explicit uncertainty | — |
| OBSERVE, RECEIPT@3 | rejected as late receipt | 1 |
| CANCEL, CANCELLED@0, QUIESCENT@1 | rejected; no observation is pending | 2 |

The finite checker honored the declared, state-dependent logical deadline and preserved the distinction between explicit `UNKNOWN` and quiescence. A hidden retry marker did not affect the externally visible verdict.

## Scope and limits

This is a synthetic protocol experiment, not a real-time timeout measurement. The two-tick bound was stipulated by the contract; no claim is made that it is an appropriate runtime deadline. The test does not cover a real scheduler/transport, GUI capture, probabilistic conformance, fairness, task effect, production ABI, or human tempo. It advances the protocol-layer hypothesis only.
