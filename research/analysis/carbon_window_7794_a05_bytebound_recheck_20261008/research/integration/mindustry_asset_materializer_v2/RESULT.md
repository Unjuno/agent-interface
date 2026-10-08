# Mindustry offline asset materializer v2 — retained first outcome

Task `MINDUSTRY-ASSET-MATERIALIZER-20260917-002`, Issue #894, base `4c5b71c51aa934b0a160aa95d42563bf5d6ab96c`.

Disposition: **`PASS_MINDUSTRY_ASSET_MATERIALIZER_MECHANICS_SCOPED`**.

The source-first frozen formal runner was invoked exactly once; formal reruns are zero. Independent audit passes every recomputed check and four post-result corruption controls are all rejected.

## One-variable repair from retained v1 failure

v1 remains retained at `0fb1404d43813d03f47b72e3d410516d50ac44a4` with `FAIL_MINDUSTRY_ASSET_MATERIALIZER_MECHANICS`. Its formal exposed that `Path.resolve(strict=False)` followed a source symlink before `lstat`, allowing a symlink-to-valid-file to bypass the intended identity boundary.

v2 changes only that semantic boundary: source paths use `absolute()` without following symlinks, then `os.lstat()` rejects links and `os.open(..., O_NOFOLLOW)` preserves the same admission at open time. The formal harness also corrects v1's non-semantic filename-order assertion.

The frozen symlink-to-valid-file control now returns `ValueError: symlink source forbidden`, leaves the final output absent, and leaves no sibling stage residue.

## Frozen gates

All nine gates pass:

- correct tiny-fixture staging publishes `ASSETS_READY`;
- manifest bytes exactly match the published file identities;
- JAR bytes/hash exact;
- save bytes/hash exact;
- published file set is exactly `MANIFEST.json`, `Mindustry-v160.2-complete.jar`, `canonical.msav`;
- wrong JAR rejects cleanly;
- wrong save rejects cleanly even after the first file had been copied into the private stage;
- source symlink rejects cleanly;
- a preexisting destination is refused without modification.

Publication remains all-or-nothing: both sources are checked as regular non-symlink files, copied and fsynced into a sibling private stage, reverified, the manifest is fsynced, the stage directory is fsynced, and only then is the completed directory atomically renamed to the final path followed by parent-directory fsync.

## Production identity metadata preserved

No production binary is included in this experiment. The helper carries forward only the frozen identities from #879:

- `Mindustry-v160.2-complete.jar`: 87,022,576 bytes, SHA-256 `7f210295dfffb4c17b582b27bab41f4dde83f557f00f0877572fdac943f40539`;
- `canonical.msav`: Git blob `7663b25633d853a257fbb407723fe85579120111`, SHA-256 `8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed`.

## Integrity / boundary

- source-first freeze commit: `378b707f56d111e3cd5096fad49cdaef747f8af1`;
- formal invocation: 1; reruns: 0;
- no provider/model/GUI/Mindustry/X11/network task action;
- result scope is offline materialization mechanics only.

This closes the materializer mechanics exposed by the v1 failure. It does **not** make the real JAR/save available in the current DNS-restricted container and does not authorize a live Mindustry run. The next execution environment should mount the two exact frozen files, run this helper against production identities, verify the resulting `ASSETS_READY` manifest, then request the separately scoped zero-model live fixture smoke. No further synthetic Agent Interface mechanism is justified by this result.
