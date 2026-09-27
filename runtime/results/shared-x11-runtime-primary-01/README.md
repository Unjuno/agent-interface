# Primary use of the shared scoped X11 runtime archive

The primary assistant used the portable runtime built from committed source
`5c42cb632a7e7f13337fbf38dd695b4877c4fe7c` for six Chromium fixture tasks on WSL/X11,
seed 991327. `runtime-origin.json` records archive paths for the bridge and
ordinary dispatch API. No helper model, new sensor or new wait default was used.
The fixture, lifecycle harness and primary-review exchange remain research code;
the guarded runtime and dispatch implementation came from the archive.

Six task images were reviewed before final independent scoring. The append-only
history contains exactly one correct token submission for each task. On task 4,
the previous layout's target refused with zero input emissions. The assistant
viewed the new image, grounded new field/Save points, and completed tasks 4–6.
All twelve successful guarded programs retained verified empty releases. The
three tracked harness processes terminated; this is not descendant-wide cleanup.

The archive test also imports the API in an isolated Python subprocess outside
the checkout and exercises matching, changed pixels, and receipt-before-next-step
ordering. The full local checks passed 223 protocol and 105 harness/distribution
tests. Earlier check-01 is retained and passed its then-current 97 harness tests.
The raw bundle includes images, decisions, receipts, history, archive, build
manifest, checks and terminal outcome. No immutable preregistration is claimed.

Run `python -O runtime/results/shared-x11-runtime-primary-01/verify.py` to verify
retained bytes, build identity, image hashes, exact effects, releases, primary
reviews before scoring, and refusal/repair boundaries without extraction or GUI.
The manifest establishes internal byte consistency, not independent authorship.

This closes shared implementation and archive availability. It does not establish
semantic text acknowledgement before Submit, general form correctness, new MCP
method exposure, matched speedup, actual model-token reduction or human tempo.

## CI integration correction

The first remote CI attempt on `18a212d8c` failed because CLI/X11 sparse checkouts
omitted the new package, and the dependency-free distribution job tried the
Pillow-dependent handle check. Full initial logs are retained in `ci-repair.tar.gz`.
Commit `d2fa7807d` adds the required checkout paths/triggers and separates the
no-site-package form availability test from the Linux dependency-bearing archive
check. No runtime input implementation changed after the exercised build.

Corrected local validation passed 223 protocol and 106 harness/distribution tests,
plus the 8 distribution tests with `python -S`, 102 CLI tests and 8 additional
X11 receipt/watch tests. The supplementary manifest and verifier preserve these
results without modifying the original 317-file primary-use bundle.
