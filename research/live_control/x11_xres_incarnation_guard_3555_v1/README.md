# XRes recycled-XID process-incarnation guard — retained evidence

Issue: [#3555](https://github.com/Unjuno/agent-interface/issues/3555)  
Allocation: `issue3555-xres-guard-formal-02`

## Result

Observed gate: `PASS_GENERATION_GUARD_REJECTED_STALE_ALIAS`. Independent raw-only audit: `PASS_INDEPENDENT_RAW_RECONSTRUCTION`, 8/8 corruption controls. Preregistration provenance: incomplete because the exact original freeze and source-manifest files matching the SHA-256 values embedded in raw were not retained. Later edited versions are not substituted. The initial auditor STOP remains in the Issue history.

## Files

- `REPORT.md` — scoped result and limitations.
- `raw.json` — immutable runner output, SHA-256 `39aee2c0614a411aefe602b9d9e7ae910b9aa5cc59796b209ca176909acd101d`.
- `independent-audit/audit.json` — independent raw-only reconstruction, SHA-256 `0a357fff35820b5f09ffd826f440df47a75f402c0c154d5690708b94d3cd3f44`.
- `FINAL_AUDIT.json` — consolidated checks and provenance boundaries, SHA-256 `b34486bb2a8aa3a4be468deef42dec7827c5495b0b8ca14b7e73358b3b01cf33`.
- `audit_rawonly.py` — independent auditor source, SHA-256 `94178c3457b21a4640eecabefdbef99dc2e05b9c8bce5c1f39af1740c9ef53f1`.
- Six `*.png.base64` files — lossless encodings of the six identical retained Xvfb captures. Decode a sidecar with `base64 -d image.png.base64 > image.png`; each decoded PNG is 2,009 bytes, SHA-256 `189a9e34def3227c5526cffb84c5ae4b854da868ad36a68b67a07891fc256701`.

Raw embeds freeze hash `4100c858b729e970a701808fcf9964ae1131efe3ccc8bf0c58db5369b546eb74` and source-manifest hash `7af1514fea3ec5746bcf5d7aae9d72debaf996810a7d8a9ec01451ef2c68e177`; their original bytes are unavailable. Do not claim a byte-verified preregistration from these hashes alone.

Scope is one research wrapper, one pinned linux/arm64 image and private Xvfb allocation. No production/default runtime, general X11, remote transport, or promotion claim.
