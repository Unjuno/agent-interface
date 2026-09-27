# Post-formal publication integrity correction (#4193)

This is a packaging/integrity erratum discovered during PR #4607 review. It does not change the frozen plan, source capsule, formal raw evidence, audit outcome, or scientific disposition.

## Corrections

- The original `PUBLICATION.json` `result_summary_sha256` (`c1d039...`) did not hash the committed bytes of `RESULT.json`. The SHA-256 of the exact Git blob bytes is `431ce475ff6428b6c7493a6c9cd301919ed88586a59e6d1f93823ac79017e3e6`; `PUBLICATION.json` now records that value.
- `SHA256SUMS.source` had the wrong digest for archived `audit.py` (`d9c37b...`). The exact `SOURCE.tar.xz` member hashes to `4055a97229681f3f2cb41998424c775b1ed1181da2200f28df39307212e3d714`, matching the preformal `FREEZE.json`; the sidecar now records the matching digest.

The original values remain available in the preceding commit history and PR review comments. `SOURCE.tar.xz`, `FREEZE.json`, `RESULT.json`, `RAW_USED.json.xz`, `AUDIT_SUMMARY.json`, and the formal outcome are unchanged.

## Independent verification

`verify_publication.py` recomputes the committed byte hashes, decompresses and hashes the retained raw evidence, opens the frozen source capsule, verifies every source member against both the corrected sidecar and `FREEZE.json`, and checks the formal HOLD/count invariants. It does not import or execute the experiment runner or audit. Its local and offline pinned-container outputs are `INTEGRITY_RECHECK.txt`; the container receipt is `INTEGRITY_RECHECK_CONTAINER.json`.

One correction-check container attempt exited 127 before running the verifier because `shasum` is absent from the pinned slim image. This tool/setup STOP is retained in `INTEGRITY_RECHECK_ATTEMPT_FAILED.json`; the next offline container invocation uses the image's `sha256sum` utility. No formal experiment or scientific allocation was rerun.
