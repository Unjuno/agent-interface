# First allocation: evidence-retention failure, not promoted

TASK: CO-TRANSPORT-INTEGRATION-20260915-01
BASE: 120a1b8de6d515d75c2200ca3acc310a124fb373
PRE-MEASUREMENT FREEZE: 0f13991aba206f1c39b2771ef002bdb203b851df
FINAL DISPOSITION: FAIL_EVIDENCE_RETENTION / HOLD_PERFORMANCE_PROMOTION

The container executed 12 integration tests against the unchanged upstream AIT1 Decoder and ImageArtifactSink; its retained tool output showed 12/12 passing. One bounded benchmark invocation then completed all 12 blocks: 288 sequences / 2304 frames. A separate posthoc aggregation and deterministic packet/PNG replay reported 18/18 checks passing. These are observations from tool output, NOT a claim that their full raw evidence is now in GitHub.

Before the first-result ZIP could be uploaded, a later container call found `/mnt/data/co-work` absent. A bounded search of `/mnt/data` and `/tmp` did not recover the working directory, raw CSV, per-frame receipts, or ZIP. The six original conversation attachments were still present. The cause of the working-directory disappearance is unknown; no claim about which process or infrastructure event caused it is made.

The attempted archive had reported SHA-256 `d1d7e650ef60a2d18fb170fe1561159cdfde0b2fbd20328da12305a9d4c37855` and size 19868 bytes in prior tool output. Its bytes are currently MISSING. A digest without retrievable bytes is not adequate retention. The first CSV had reported SHA-256 `d236ea97d4aef7f0be9f94d1034db71dfb122b6cc9d67552f666118a4f74ee13`; its bytes are also MISSING. Do not synthesize those files from medians or fabricate matching artifacts.

## Observed but not promotable timing summary

These rounded numbers are transcribed from the completed tool output only. They cannot substitute for the missing raw records. Eight-frame encoder -> decoder -> PNG-publication sequence medians, milliseconds:

| Synthetic condition | O1 | O2 | prior V1 | candidate V2 |
|---|---:|---:|---:|---:|
| Repeated shared buffer | 15.347 | 15.156 | 14.618 | 14.662 |
| Repeated copied buffer | 15.326 | 15.023 | 14.397 | 14.315 |
| Sparse random background | 193.731 | 195.461 | 142.437 | 140.362 |
| Dense scroll | 111.106 | 186.310 | 117.560 | 118.256 |
| Dense random | 190.375 | 257.948 | 195.359 | 198.872 |
| Sparse header counterexample | 1.835 | 3.936 | 4.318 | 4.598 |

Observed negative condition: the sparse header counterexample used 1802 bytes for V2 versus 1336 for O2. Thus sparse change count did not imply smaller compressed packets. Dense conditions still favored O1. The repeated steady-codec gate reported PASS, but full-pipeline shared-repeat timing was slightly worse than V1. No default route change, GUI speedup, model-token gain or causal task benefit follows.

Reported environment: CPython 3.13.5, NumPy 2.3.5, Pillow 12.3.0, zlib 1.3.1, Linux x86_64, Intel Xeon Platinum 8370C, sampled 2793.436 MHz (not fixed), 5 visible CPUs and 4 GiB cgroup memory limit. Twelve balanced blocks, four arms, six deterministic synthetic inputs, eight frames per sequence. Most inputs were 384x256 RGB / 64-pixel tiles; header counterexample was 8x8 L / one-pixel tiles. Times excluded capture, network/model work, hashing, post-publication verification and log serialization. No GUI or model calls occurred.

## Required disposition and successor

- Retain this loss as a failed allocation outcome. The numerical first result is not formally retained, despite earlier mechanics/audit output.
- Never rerun this ID or regenerate a purported first-01 archive. Historical v1 attachments are unchanged.
- Publish recoverable code and the already committed hash freeze. Code reconstruction must match frozen hashes; unmatched reconstruction is a new version, not the executed source.
- Re-run deterministic unit/integration tests only as explicitly new construction validation, with a durable transcript. This is not a replacement performance allocation.
- Any later performance measurement needs a new ID and a changed retention protocol: durably checkpoint source, complete raw records and manifest before promotion. Preserve failure even if a later allocation succeeds.
- Keep candidate opt-in. No shared runtime/workflow/DOOM recovery file is changed by this lane.
