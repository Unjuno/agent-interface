# A11 environment setup

The guest reads the clean exact-current-main checkout mounted from the dedicated Issue #59 host allocation root at `/mnt/source`. The runner derives the guest checkout path from the host repository path and refuses to launch unless OrbStack reports the expected root mount. The VM is `issue59-live-v39-a01-20261009`; A11 uses its own source checkout at `/mnt/source/results-local/doom/a11-source` and its own unique output path. A08–A10 source trees and evidence remain untouched.

Before creating `FREEZE.json`, the one-shot runner verifies current `origin/main`, ancestry, clean experiment tree, all runtime-source hashes, the mount mapping, fixture and WAD hashes, app-server CLI identity, ViZDoom/Pillow/Python/Python-Xlib/openpyxl versions, Xvfb size, at least 2 GiB of available memory and `/tmp` disk, and absence of active game/display processes. Any failed preflight stops before app-server or guest execution.

The guest and host share the A11 allocation output directory through the checkout mount. Guest image-path receipts bind each image file's bytes and relative output path; the host independently checks those bytes before forwarding a `localImage` request. This allocation is one-shot; it has no retry or in-place repair.
