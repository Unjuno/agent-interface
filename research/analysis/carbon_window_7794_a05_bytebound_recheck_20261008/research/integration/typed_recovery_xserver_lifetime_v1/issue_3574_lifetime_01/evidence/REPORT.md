# Issue #3574 — X-server lifetime identity replication

## Result

`PASS_XSERVER_LIFETIME_BINDING_REQUIRED_SCOPED` on one pinned linux/arm64 OrbStack image, one formal runner invocation, four fresh G1/G2 Xvfb pairs and zero retries. No input/action/model calls occurred.

Every pair recreated top-level XID `2097152`, root XID `1293`, geometry `[80,80,240,160]`, `transient_for=KNOWN_NULL`, and the exact same 153,600-byte XGetImage buffer (SHA-256 `3684d961cbc0f94068c83eacad403339c0672cc525500360581f42460562bb56`). XRes 1.2 `LocalClientPID` tracked each current fixture process; p1/p2 PIDs and `/proc` start ticks differed in all four pairs, and all eight Xvfb plus all eight fixture processes were reaped with their X11 sockets removed.

| Policy / comparison | Outcome |
| --- | --- |
| CURRENT_TYPED, same generation | EXACT_MATCH 4/4 |
| CURRENT_TYPED, stale across X-server restart | EXACT_MATCH 4/4 |
| LIFETIME_BOUND, same generation | EXACT_MATCH 4/4 |
| LIFETIME_BOUND, stale across X-server restart | REJECT 4/4 |

The unchanged #881 typed identity alone therefore aliases across the tested X-server reincarnation. Adding the opaque observation-side `server_instance_id` discriminates that stale identity while preserving same-generation identity classification in this controlled fixture. Six negative controls per pair (24 total) failed closed. The raw-only independent audit passed all 16 rows, source/image/raw hashes, all eight process lifecycles, and pixel bytes. Seven posthoc corruption probes against separate copies detected denominator, XRes PID, pixel, lifetime token, authority/input, cleanup, and freeze-manifest tampering; the formal raw was never edited.

## Provenance and evidence

- Source commit: `61311817969251b814cb00b568a75c91a3591d3e`.
- Exact #881 validator Git blob: `91983ab78a06b93cc7fdd829b6094fd255f18210` (frozen copy byte-equal).
- Freeze-manifest SHA-256: `b216042ce7ad3194b44ac25368c6143b4900e6400e6a7fa0b4ef7c641e7bea60`.
- Container: `agent-interface-3548-routes:20260920`, `sha256:76af6aaaab4419b3f799f3121aab191a347130cad07080ac285e3b6d9896cefc`, linux/arm64; formal `--network none`, read-only freeze mount.
- Uncompressed raw SHA-256: `1d22b471d6d3e431f44519fe1e99360ba16506430374c5ed1f154d4be1a89fcb` (1,696,646 bytes). `raw.json.gz` is lossless; decompress and verify against `raw.sha256`.
- Independent auditor: SHA-256 `f2e53076aeecf2ac2570afb8aafc6673caaab2bbf62905b11065793c5922a503`; audit result `independent-audit.json`.
- Corruption probes were a post-formal auditor-quality check on temporary copies, not extra X-server allocations; raw hash remained identical.

## Scope boundary

This identifies a lifetime dependency of the #881 typed identity under deterministic private Xvfb restart. It does not implement a production token issuer/storage API, change the default runtime, grant action authority, test remote X11/Wayland, prove crash persistence, or establish production security or task/performance benefit. The predecessor #902 8-row comment, its separate scoped result, and #3555's provenance-incomplete XRes guard result remain unchanged; this successor corrects neither historical record.
