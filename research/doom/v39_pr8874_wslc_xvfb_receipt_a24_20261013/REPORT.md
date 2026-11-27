# V39 adapter-to-analyzer receipt integration A24

## Result

`FAIL_AUDIT`. One actual XTEST lowercase `w` key traveled through the current-main V39 backend's `raw()` and batch-publication methods into the current-main V4/V12 owner on private Xvfb. The observer received KeyPress then KeyRelease for keycode 25 on window 2097152; server keymap was down while held and up after release. The backend published a top-level owner-bound admission. It retained that exact row and, after checking the one-to-one key/owner/token/deadline identity and admissionÅ®acknowledgmentÅ®release time order, attached it to the batch release with `operation="down"`. V4/V12 supplied one matching owner-thread KeyRelease/XSync/keymap receipt; the adapter marked the completed release batch verified. The unchanged analyzer accepted exactly one hold with zero malformed, unmatched or invalid receipts. Owner cleanup was verified empty, the thread stopped, Xvfb exited 0, and WSLc removed the container.

The RED-GREEN sequence is preserved: A22 failed with an unmatched admission, A23 attached it but failed the analyzer's explicit operation requirement, and A24 passed after adding that canonical field to the already validated linked copy. None of these prior raw records were overwritten or rerun.

## Limits

The single-step adapter methods and current owner/analyzer sources were exercised; the test injected only an abstract parent backend because the cached Xvfb image does not include the game-specific dependency. The outcome validates receipt composition for this path, not Doom/MAP01 effect, application response, model control, threat exposure, finite recovery under failure, or physical input. No live/formal allocation was consumed. WSLc reported unsupported swap/cgroup memory limits; no hard cap is claimed.

Conditions and source hashes: `PREREGISTRATION.md`, `SOURCE_MANIFEST.json`. Raw SHA-256: `d0962f52d5aee479e46c24ff5770b81a9e81767d60ebaa552f5fadb09255ba25`. Independent per-check audit: `results/a24-01/audit.json`. Complete command output and before/after container state are preserved alongside raw. The code change remains an experiment snapshot; no main/runtime source was modified.
