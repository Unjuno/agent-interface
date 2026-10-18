# PR #8065 post-repair owner identity check (A02)

Result: **FAIL_REPAIR_INEFFECTIVE_AT_4158d9b** for the startup owner-identity gate. The post-repair V15 plus per-key route still selects `research/live_control/input_owner_v12.py` (SHA-256 `01c41f5a…eab9df`) while `sources.json` records the archived A01 owner SHA-256 `b63e8a92…5c1508`. V12 plus per-key selects the archived owner correctly, and default V15 retains the release-batch backend chain with its V4 owner binding.

The test froze 56 production source files from PR #8065 head `4158d9b063e7cbf56828f1b0667ec2714af0ff2b`, then ran each route in a fresh Python process. All three exited 0 at the `suite.Session` construction boundary; the harness blocked X, game, process/thread startup, image capture, and workbook construction. The host lacked Pillow, NumPy, and openpyxl. No packages were installed; the probe supplies inert import stubs for those import-time dependencies and refuses calls that could cross the boundary. The first two construction failures are retained under `run-20261005T01/` and `run-20261005T02/`; the corrected bounded run is `run-20261005T03/`.

`audit_readback.py` independently verifies all 56 frozen source sizes and hashes, the three exit receipts, stdout/result identity, stop conditions, and the predeclared route gates. It passes 11/11 checks and reports the expected repair failure. That is a source-selection result only. No Session or InputOwner object was constructed; no GUI, game, input, physical release, provider timing, task effect, or live threat exposure was measured. The live Issue #59 lane remains outside this evidence.

The test does not establish whether the resulting owner causes lost UP measurements during execution. That consequence requires a separately authorized, appropriately bounded runtime test; this A02 does not perform it. No runtime code is changed by this evidence package.

Reproduce with Python 3.12+:

```sh
python research/doom/v15_perkey_import_59_e0cc_20261005/postrepair-a02/replay_startup.py /new/output/path
python research/doom/v15_perkey_import_59_e0cc_20261005/postrepair-a02/audit_readback.py
```
