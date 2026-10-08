# Allocation -01 report — Issue #5198

**Disposition: `STOP_AUDITOR_IMPLEMENTATION_DEFECT`. No scientific decision is available.** The frozen runner completed once and produced a canonical 4,800-row heldout result. The separately frozen raw-only auditor ran once, rejected the result with `independent_reconstruction_mismatch`, and exited 1. Do not repair the auditor against this consumed allocation, rerun it, regenerate these seeds, or treat runner metrics as independently verified evidence.

## H / T / D / C / U

The question was whether typed-mode posterior aggregation retains a wrong-emission advantage over direct classification after each arm's confidence threshold is independently calibrated to 65% pooled coverage on a distinct calibration sample. Training, calibration and test used disjoint seeds 67010231/67010232/67010233; the two arms shared all generated rows. The frozen source is in `FREEZE.json` (source commit `668b888a47ddfbb1a50e1dd9ff3a386836b22484`; freeze SHA-256 `abfc648a7599af3e041eceb5b8817a8a088bd91368d318f9b87a40f21b2963bd`).

Docker Desktop `desktop-linux`, Engine 28.5.1, pinned image config digest `sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a`, linux/amd64. Runner container `1f3f920f12dae45876a38098ecdca8c2b8413dcdf02c2d025e333e88c9f36663` exited 0. Raw `result.json` is 2,794,446 bytes, SHA-256 `b55b8d9e58497c47ef5a2152d1236d27fdb6918a018cbeebf2a75f0b5f709470`.

Separate auditor container `f5ce71743b7cb13cb2142230fa20a80612f7bcb2843e1cf9762aa8a2a6855d61` exited 1. Its receipt confirms the raw hash and row counts and rejected 16/16 directed mutations, but reports `pass=false`, `errors=["independent_reconstruction_mismatch"]`; it did not emit a scientific disposition.

### Failure diagnosis

Static inspection of the frozen source explains the deterministic mismatch: both runner and auditor use tuple-valued feature vectors/configuration when constructing Python objects; the runner serializes those tuples to JSON arrays, and `json.loads` in the auditor reads arrays back as Python lists. The auditor then compares the parsed object directly with a newly reconstructed object that still contains tuples (`observed != reference`). The frozen auditor consequently rejects semantically identical canonical JSON before its intended exact-reconstruction check can pass. This identifies an auditor implementation defect, not an experimental result about matched selective risk.

The auditor's 16/16 corruption-control count does not cure the failed base equality check. No post-hoc normalization or alternate auditor was run. The sole formal seed allocation is consumed; any corrected auditor or further scientific test requires a separately preregistered successor with fresh seeds and a construction test that includes JSON round-trip normalization.

## Scope

No claim is made about calibrated selective risk, GUI diagnosis, runtime authority/safety, model quality, task effect, latency/tokens, cross-app transfer, human tempo, or product readiness. Allocation -04 (`HOLD_COVERAGE_TRADEOFF`) remains unchanged and was not pooled with this STOP.
