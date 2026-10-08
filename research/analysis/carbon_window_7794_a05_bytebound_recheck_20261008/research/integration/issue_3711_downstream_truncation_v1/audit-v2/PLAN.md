# Post-run evidence-binding audit v2

Audit allocation: `issue3711-downstream-truncation-artifact-audit-v2-01`.

- **H:** The v1 audit validated copied request/report files and raw hashes, but did not independently bind those copies to the retained `attempt/` directory or to the file hashes emitted by actual `attempt-status` recovery.
- **T:** Without rerunning the CLI experiment, read the frozen formal-02 bundle and source read-only. Recompute the complete attempt-directory snapshot; byte-compare its request/report to the published copies; bind recovery stdout's per-file hashes/values to those actual bytes; independently parse full accepted JSON and truncated downstream bytes; recheck all source hashes and v1 audit/raw digests.
- **D:** One new isolated OrbStack Docker Python 3.12 linux/arm64 container, pinned image from the original freeze, `--network none`, read-only source and formal evidence, separate writable audit-output mount. No dispatch/backend is called.
- **C:** PASS only if every source, artifact, directory snapshot, recovery-field, and truncation predicate agrees. Otherwise report a v2 audit failure; do not edit or replace v1 raw/audit evidence.
- **U:** This is a post-run artifact-integrity audit only. It does not repeat the experiment, establish OS/network transport behavior, or add live task evidence.

The v1 allocation result and auditor remain byte-for-byte historical evidence. This v2 audit is an additive independent check prompted by review of the first auditor's evidence binding.
