# Issue #5134 — OrbStack cross-process publication result

**Disposition: `PASS_ORBSTACK_CROSS_PROCESS_PUBLICATION_SCOPED`.** The exact
formal allocation `needle-publication-orbstack-bind-5066-20260928-03` completed
one runner container invocation and one separate raw-only auditor invocation.
Both exited 0. The predecessor construction pilot's `STOP_BOUNDARY_PILOT` is
preserved unchanged; this is a fresh allocation with a corrected, frozen audit
contract, not a replay of that pilot or of allocation -02.

## Frozen execution identity

- Issue: #5134; owner and queue markers: #5074 comment 5907347101 and #5085
  comment 5907349034.
- Source commit: `8af08b23363c84bdd5afc3be66fdd78da63ec094`; source tree:
  `e959884ca6f40d738f1524a12e25380c489a6fa5`.
- Frozen main: `eddcf7a47c1f3c47165288037e66f66da0c3138a`.
- Freeze SHA-256: `1ce9ac2136b04a0f84a9ff2f3999bd49bc1abd7127b158012669d5a00cb1823f`.
- Host: macOS 26.6.2 arm64; Docker context `orbstack`; image
  `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`
  (`linux/arm64`). Formal source/output mounts were read-only/read-write;
  auditor `/src` and `/in` were read-only and `/out` writable. Both containers
  exited normally without OOM or runtime errors.
- Seed: generation 3788, blob
  `45b80150dac503f4eb6f3cb5d82f9afa2c587107`, SHA-256
  `2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a`.

## Observations and gate

The raw bundle contains 28 atomic concurrent rows, 28 exact post-publication
rows, and 28 matched unsafe in-place rows. Each of seven transitions has four
rows in each category. All four readers in each arm exited 0. The independent
auditor reconstructed the raw observations and receipt with `errors=[]` and
accepted all 11 corruption controls.

The invalid-digest proposal returned `YIELD_INVALID_CANDIDATE`; the stale-base
proposal returned `YIELD_STALE_GENERATION`. Both left ACTIVE at generation 3795
with the same before/after SHA-256. Raw records `authority_granted=false`,
`dispatch_count=0`, and exactly one formal invocation. These results satisfy
the frozen scoped decision gate for this allocation.

## Retained artifacts

All runner and auditor outputs, raw bytes, receipts, container inspect records,
mount records, input manifest, audit result, and hashes are retained unchanged
under `results/formal-01/`.

- `raw.json` SHA-256:
  `43433e199b9836e4b67a39a0913ed2095cacc5b53dabecd1a5a63ae1f7c7bfb2`
- `invocation_receipt.json` SHA-256:
  `059949de0ec25f9be2effe82b816ba0e5b4de5a9dd9a68bfb2da41aefbb3b06c`
- `audit-output/audit.json` SHA-256:
  `8bdf8cd2f9e07fba3526f8c972d34d755e85ca75826fd4a073c5e4ba925a0b90`
- `execution.json` SHA-256:
  `41382a359f5185de631246f23c3da87952a2106aac6d752b0ab3456bfaf34845`

The claim is limited to this synthetic schedule, one macOS/OrbStack host,
Linux/arm64 image, and bind path. It does not establish crash durability,
other host filesystems/platforms, production safety, GUI/model/task quality,
dispatch authority, or latency.
