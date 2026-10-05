# Reading and reproducing the construction evidence

This archive is inert. Python source is retained with a `.py.txt` suffix so repository test discovery cannot run the harness. The ordinary synthetic constructions may be reproduced in a fresh private directory; this does not authorize replay of any formal allocation or real game/X session.

For an exact recorded variant, select one successful run, such as `full-04`. Combine its `parent-loaded-sources.json` and `external/loaded-sources.json`. Each path/hash pair is mapped by `source-closure.json` to an exact retained blob. Check the SHA-256, then restore that blob at `source/<original relative path>` in the private directory. Restore the two `nonpython-source/` files under `source/research/doom/`. The loaded-source records from different runs can legitimately contain different controller or monitor hashes; do not silently mix variants.

Restore the selected run's `probe_controller.py.txt`, `child_session.py.txt` and `fake_environment.py.txt` as `.py` files beside `source/`. Use Python 3.12 with Pillow and NumPy. The recorded run used the existing Codex bundled Python on macOS 27.0.1 arm64, with OMP_NUM_THREADS and OPENBLAS_NUM_THREADS set to 1 in the child environment. No packages or services were installed. Use a new, nonexisting output directory name in place of `<fresh-output>`:

```
python3 -B probe_controller.py <fresh-output> normal
python3 -B probe_controller.py <another-fresh-output> hard_change
python3 -B probe_controller.py <another-fresh-output> unknown_change
python3 -B probe_controller.py <another-fresh-output> failed_release
```

Each invocation uses one real local child Python process and only synthetic external seams. The harness records its own version before startup, bounds the parent construction to 35 seconds, and reaps its child. `failed_release` intentionally exits nonzero and retains a fake key as down; its required result is no further model turn/submit and an explicit incomplete-cleanup receipt. Do not change that result into neutral release.

To inspect retained results without executing controller code, restore `audit_runs.py.txt` to a private `.py` path and pass the archive directory as its sole argument. It reads the four recorded `full-04`–`full-07` directories, computes raw RGB hashes and event/identity checks, and writes a new audit file under the supplied directory. Copy the archive first if preserving it byte-for-byte. It does not import the production receipt projector.

Scoped suite commands, exit codes and test source hashes are in `scoped-tests-01/receipts.json` and `scoped-tests-02/receipt.json`. Bare legacy module names require `research/live_control` before `research/doom` on PYTHONPATH. The originally reversed order and its import failure are retained rather than overwritten. Production controller CRLF and executed export LF differ only in line endings, as separately checked in `line-ending-equivalence.json`.
