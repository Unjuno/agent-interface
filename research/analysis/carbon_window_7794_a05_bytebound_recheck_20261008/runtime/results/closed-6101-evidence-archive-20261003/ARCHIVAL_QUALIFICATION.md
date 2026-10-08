# Closed #6101 evidence archive qualification

This directory qualifies the byte-preserving archival copy of three historical
result packages recovered from remote branch
`integration/explicit-stopped-observe-20261001`, whose observed tip was
`f797619abb89dacc9c5842edba63e81674bb8db5` on 2026-10-03. The source tip is
retained; this archive does not delete or rewrite that branch.

## Scope and provenance

The archive contains only these existing result packages:

- `runtime/results/stopped-results-01/` (110 tracked files)
- `runtime/results/stopped-observe-01/` (108 tracked files)
- `runtime/results/stopped-inspection-publication-01/` (9 tracked files)

All 227 copied Git blobs match the source commit exactly. Each package's
committed `SHA256SUMS` ledger also verifies. The JSON/JSONL corpus parses (149
JSON files and 57 JSONL records). Original package contents, including their
historical README, verifier, results, and logs, are unchanged.

The source branch also contained three `runtime/host_v1` source/test files and
a separate `runtime/results/integration-eligibility-6074-01/` package. They are
deliberately excluded: executable code is not being adopted here, and #6074 is
a distinct review scope (`HOLD_RUNTIME_INTEGRATION`) that must be qualified in
its own package. The exact selected result paths were absent from current main
before this archive was prepared. The related #6077 parent is now merged; the
historical README statements that it was pending describe the state when those
records were produced, not current PR status. Follow-up PRs #6467 and #6482
remain separate current-main work and are not represented as validation of
these archived result packages.

## Offline audit performed for this archive

The original `verify.py` scripts hard-code artifact reads under
`/var/tmp/agent-interface-evidence-storage-main/`, which is not present in a
fresh checkout. To avoid modifying the retained records or verifier, copies of
the two self-contained packages were staged under a temporary directory. A
read-only `Path.read_bytes` mapping redirected only those legacy absolute-path
reads to byte-identical files in that temporary copy; the original verifier
source was then executed unchanged. Both `stopped-results-01/verify.py` and
`stopped-observe-01/verify.py` passed under normal Python and `python -O`.
Verifier-generated `audit.json` files were written only into the temporary
copies and are not part of this archive.

These are finite consistency/mutation audits of already stored artifacts, not
a rerun of the candidate, live allocation, native X11/WSL environment, or a
current-main integration test. They support only the bounded historical
claims in the source records: one recorded Save and acknowledgment in each
session, preserved STOP, and the recorded read-only follow-up behavior. They
do not establish universal safety, adoption of the proposed runtime helpers,
causal latency/efficiency improvement, human-tempo improvement, token savings,
or billing attribution. No model tokens or billing data are attributed.

## Repository disposition

PR #6101 remains closed and untouched: its recorded head was
`2ade22fa1d753cf509ac27c8567d935d8fbe82c2`, which does not match the observed
remote branch tip. This evidence-only archive neither reopens that PR nor
adopts its implementation. Issue #5256 remains open for the separate
current-main adoption question. No branch deletion is authorized by this
archive; retain source refs until their remaining code and #6074 contents have
their own explicit dispositions.
