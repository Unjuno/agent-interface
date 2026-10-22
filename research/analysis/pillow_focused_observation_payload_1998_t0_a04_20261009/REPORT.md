# Issue #1998 A04 — Pillow PNG focused-payload result

**Disposition: `PASS_METHOD_SCOPED`.** The frozen candidate exited 0 after one invocation, emitted structurally complete 441-case JSON, and the independent standard-library raw auditor exited 0 after one invocation. Retries: 0. The allocation is consumed.

## Observed finite result

Across 21 retained 1280×800 RGB frames from Calc, Chromium, Inkscape, and xterm, the audit reconstructed all 21 full-frame PNGs and all 441 crop PNGs exactly against the archived source pixel digests. The candidate used the main-branch `ImageArtifactSink` source at Pillow 12.3.0 and `compress_level=6`.

All 420 fixed smaller crop requests (four exact crop areas at five placements per frame) had strictly smaller canonical JSON+base64 payloads than their corresponding full-frame representation. The savings-only selector chose a focused payload in 420/420 cases. The 21 full-bounds focus controls all fell back to FULL_FRAME because added focus metadata could not produce a strict size reduction. Six of six frozen mutations were rejected.

For the 441 authored requests, repeating the full-frame baseline costs 15,770,790 serialized bytes; selected representations cost 6,153,387 bytes, or 9,617,403 fewer bytes in this finite matrix. These are byte counts from the declared JSON/base64 schema. They are not model tokens, network transport, latency, or task utility measurements.

## Custody and reproduction

- Base: `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`.
- Source construction commit: `f17a20676c8c87a37b11faa409c1707d05c77236`.
- Freeze commit: `e0f465046664bab0b6d05c38a6f2172044494ed0`.
- `FREEZE.json` SHA-256: `b6a266965ae0aee8f2485e44dd9b140356727901c500f334b7a0e08fd1b18b57`; all 38 frozen source/runtime/ledger/frame entries verify.
- Candidate stdout SHA-256: `4afca7ffffd3625b74af4889900fe2e2ef22f118236660653c15bf73f37c243f` (309,727 bytes). Candidate stderr is empty.
- Auditor stdout SHA-256: `adc0d023ecc4a1f7277a8f4a4031df31546ee383b2427579e4ca3c89478f6f64` (1,240 bytes). Auditor stderr is empty.
- Output artifacts: 21 full PNGs and 441 crop PNGs, each retained and listed in `OUTPUT_SHA256SUMS.txt`.
- Host: macOS 27.0.1 arm64, Codex bundled Python 3.12.14, Pillow 12.3.0. OrbStack image inventory failed before listing images (`containerd` content blob `operation not supported`); no container was started. Both formal commands ran under macOS `sandbox-exec` with `(version 1) (allow default) (deny network*)`. This is host-only evidence, not container evidence.

## Claim boundary

This result supports only exact serialized-byte savings for these archived GUI frames, encoder version, metadata schema, and frozen crop requests. The ROI locations were authored fixtures. The result does not test whether a crop preserves task-relevant context, whether a model can use it, how an ROI would be selected live, or whether focus changes model tokens, transport, latency, authority, GUI correctness, task effects, human tempo, or product success. A02, A03, and this A04 remain separate allocations and are not pooled.
