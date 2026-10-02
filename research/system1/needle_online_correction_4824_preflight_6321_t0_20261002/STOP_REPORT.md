# Construction-runner STOP record

Allocation `NEEDLE-ONLINE-CORRECTION-4824-CONSTRUCTION-20261002-01` did not receive a complete formal run receipt. The one OrbStack `docker run` returned exit 1 after the generator and auditor had produced `data.json` and `audit.json`; the runner then raised `KeyError: 'image_id'` because `FREEZE.json` stores the image under `image.id` and the runner expected a flattened key. No retry or rerun of the generator is permitted under this allocation.

Preserved files under `results/preflight-01/`:

- `data.json`, 123,117 bytes, SHA-256 `dad06f71a4a7acfd4ce110852ce5ee82f5e2ce654e1cf0f1d4401106f2edd188`.
- `audit.json`, 597 bytes, SHA-256 `a3738b35a2100838a7819a08d138c067ae10bfba32df3a8d5c97100fbaa44b07`; it records `PASS_LABEL_PREFLIGHT_SCOPED`, 984 rows, three seeds, no baseline errors, and 7/7 mutation rejections.
- Container ID file, SHA-256 `c13b5e86e9dfdbed4642e48ac1f585fada26ddb1025ceee84f4cbce11fda4080`; the `--rm` container exited and is absent from the subsequent inventory.

The source control flow establishes that generation returned 0 and the auditor ran once; the retained audit predicates imply the auditor's intended exit condition was 0. However, the top-level runner failed before persisting either child exit code/stdout or a `RUN.json`. Therefore the official disposition is `STOP_RUN_RECEIPT_POSTPROCESS_KEYERROR`, not PASS or scientific FAIL. The audit JSON is provisional evidence until a separately allocated independent read-only audit of the immutable `data.json` completes.

No model, optimizer, CUDA, GPU, GUI, network, or WSLc action occurred. No pre-existing container was modified. The formal RTX 3080 WSLc window remains ungranted and no training was started.
