# Rescue qualification — Issue #6354 A02 (2026-10-03)

This additive note keeps the earlier host report and supplemental WSLc report
distinct. No candidate, auditor, or training command was rerun for this rescue.

## Preserved records

- The host A02 package and the separate WSLc validation package are copied from
  PR #6697's source branch head `ccf07142c62ec46e57e4ab04b1b6f79b0208bb2f`.
  The 16 source-path Git blobs are preserved unchanged.
- The host package records one host candidate and one separate host auditor,
  both with `PASS_PROBE_CONTRACT_SCOPED`, for three seeds. The corrected probe
  labels are A=0/B=1, with recorded overlap counts 104/102/105.
- The supplemental WSLc package records an 8/8 construction suite, one
  candidate and one separate auditor, zero retries, and the same raw/audit
  SHA-256 values as the host package. Its report records WSLc 3.0.1.0, pinned
  `python@sha256:f77ac9e…`, network disabled, read-only source, 0.25 CPU, and a
  kernel warning that swap/cgroup memory enforcement was unavailable.
- The source dataset remains the allocation-01 dataset already on main; its
  recorded Git blob is `a11d8f9d231a035e65b7bc78b4b1a8e7cb5d9285` and canonical
  JSON SHA-256 is `5865040abbc60d79f138e81bf7e06bf6f885e66b5e29c9810ea8f599bad77685`.

## Independent checks and limits

The committed SHA256SUMS ledgers are checked against the copied files; the
host and WSLc raw/audit bytes are compared directly, and the source dataset
identity is checked read-only. These checks establish stored-byte consistency,
not that a container ran. The supplemental packet does not include a separate
engine/container inspection receipt; its WSLc invocation details and status
remain the claims recorded in its report, not independently re-created here.

This is only a synthetic probe/data-contract construction result. It does not
record a LoRA fit, optimizer/CUDA call, formal #6354 candidate/auditor, model
quality, forgetting, or real-task effect. Allocation-01 remains unchanged and
Issue #6354 remains open for its separate formal question. Do not pool this
probe validation with the formal allocation or infer product efficacy.
