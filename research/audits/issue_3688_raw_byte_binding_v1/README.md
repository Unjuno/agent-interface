# Issue #3688 — exact raw-byte binding

## H/T/D/C/U

- **H:** The #3676 structural auditor can accept a JSON-equivalent byte mutation because its freeze's expected predecessor raw SHA-256 is not compared with the raw file bytes. The raw file must be exactly bound before a structural PASS is possible.
- **T:** Use exact Git-object copies of #3675 raw/freeze and #3676 study freeze/auditor/tests. In one frozen local Docker matrix, check exact raw, whitespace-appended raw, altered-event raw, changed and malformed expected raw digests, changed source-manifest digest, modified predecessor freeze, and modified source bytes. Run every row through direct and CLI paths, preserve all copies/results, then independently verify them in a second fresh container.
- **D:** PASS only if the original raw passes all pinned raw/freeze/source checks and structural audit; all seven tamper variants fail before structural PASS in both direct and CLI paths; outputs are equal; the independent auditor reconstructs each mutation and receipt; hashes, container exits, and cleanup reconcile. A tampered raw PASS is FAIL. Container/hash/source setup failures are STOP.
- **C:** Audit-only. Local OrbStack Docker Engine 29.4.0, Linux/arm64, pinned image, `--network none`, read-only rootfs/input mount, isolated output mount. No X11, GUI, native input, model, or expanded XRes/product claim.
- **U:** This finite tamper set does not establish arbitrary audit completeness or broader file-provenance guarantees.

## Frozen inputs

The exact #3676 Git-object copies are under `inputs/`. Their expected SHA-256 values are in `FREEZE.json`. The upstream study freeze's own SHA is pinned at `c038b0b2f5a1c1498613b2b8986d84f70dfc49dfc4e52b051bebe0de5e1deff8`; its declared raw, predecessor-freeze, auditor and test-source digests are checked before the upstream structural checker can return PASS.

## Scope boundary

This verifies byte provenance for one retained offline audit bundle and seven bounded tamper cases. It does not rerun or invalidate the #3675 OrbStack/XRes experiment and does not imply complete arbitrary-tamper resistance.
