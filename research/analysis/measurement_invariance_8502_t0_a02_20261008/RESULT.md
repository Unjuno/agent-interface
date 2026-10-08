# A02 audit-only result — `FAIL_AUDIT_ONLY`

A02 read the immutable A01 package and did not rerun either A01 program. It validated the A01 file identities and preserved the A01 `FAIL_METHOD` signature. Its separate calculation emitted the candidate class map F01 `COMPATIBLE_SCREEN`, F02 `THRESHOLD_NONINVARIANCE`, F03 `LOADING_PATTERN_NONINVARIANCE`, F04 `STRUCTURE_NONINVARIANCE`, F05 `UNCERTAIN`; all five semantic mutations and the changed-input digest control were rejected.

The A02 gate nevertheless failed: `FREEZE.json` records the README digest as `68b80270552f49c553fbb8234cd3c6eb05b0c278b4b8abd8bdcef987c449b2`, while the actual frozen README SHA-256 is `68b80270552f49c553fbb8234cd3c6eb05b0c278b4b8abebbd8dcef987c449b2`. This is an A02 freeze-manifest error. The only audit invocation is retained in `AUDIT.json`; no correction or rerun was made.

This output is **not** `PASS_AUDIT_ONLY_SCOPED` and does not repair A01's failed audit. The diagnostic class map is not promoted as independently verified evidence because A02's own source-integrity gate failed. No candidate, WSLc/container, model, GUI, GPU, participant, or network work was performed in A02.
