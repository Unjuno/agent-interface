# A09 environment setup

The guest reads the same clean current-main checkout mounted from the host allocation root at `/mnt/source`. The runner derives the guest checkout path from the host repository path and refuses to launch unless OrbStack reports the expected root mount. The VM is `issue59-live-v39-a01-20261009`; this is the dedicated Issue #59 VM, not the shared CI VM.

Before the one-shot runner creates `FREEZE.json`, it verifies current `origin/main`, ancestry, clean experiment tree, all runtime-source hashes, the mount mapping, fixture and WAD hashes, app-server CLI identity, ViZDoom/Pillow/Python/Python-Xlib/openpyxl versions, Xvfb size, free memory/disk, and absence of active game/display processes. Any failed preflight stops before app-server or guest execution.

The guest and host share the allocation output directory through the checkout mount. Guest image-path receipts bind each image file’s bytes and relative output path; the host independently checks those bytes before forwarding a `localImage` request.
