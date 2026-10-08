# Evidence recovery of closed PR #6796

The three A01/A02/A03 packages are retained unchanged from remote tip
`c5ad94b9e84e7d28fd41f02c2ac699bbe5e54eed`. PR #6796 was closed without
merge because its broad T0 hypothesis had already been tested in the earlier
WSLc T0-01. This recovery archives historical evidence; it does not reopen
that experiment or certify a new research advance.

- A01 remains construction/environment STOP, with no formal invocation.
- A02 remains preformal launch STOP caused by a truncated image digest, with
  no formal invocation. Empty launch artifacts are retained as they were.
- A03 retains one candidate and one auditor invocation, exit 0 and scoped
  finite-method PASS on ten authored rows, seven harmful cases, zero candidate
  false admissions, ordinary-valid-control admission, and UNKNOWN for the
  rare safe state observationally identical to a harmful state.

The original report does not itself explain the duplication discovered later.
The closed PR's final lineage correction controls interpretation: A03 is a
post-hoc independent replication, not the first test, not a preregistered
matched-runtime comparison, and not runtime equivalence. Ten rows/seven harms
are not directly comparable to the earlier six held-out states/eleven audit
cases. None demonstrates real-skill, GUI, user, production-safety or latency
benefit. No fresh allocation or formal command was run during recovery.

## Missing remote logs recovered

The original worker checkout
`/Users/taka/Documents/Codex/2026-10-03/agent-interface-6645-guard-refinement`
still had the exact source HEAD and clean tracked files. Its four ignored A03
stdout/stderr logs were copied unchanged into their original paths. Every
log matches the SHA-256 already recorded in the original source manifest;
both stderr streams are empty. All 36 manifest entries now verify, including
the previously missing logs. This binds them to the published manifest but
does not add independent host-attestation evidence.

## Recovery-only checks

The unchanged A02 construction suite passes 13 tests locally. New archival
tests hash the entire retained manifest and reconstruct the stored audit from
the already-retained raw through the original checker function, without
invoking either formal wrapper or writing any original output. These are
retrospective integrity/replay checks, not another formal candidate/auditor
run. A01/A02 STOPs and A03's historical limitations remain intact.

The first local public-navigation check failed because the new package paths
had not yet been staged, while that checker uses `git ls-files`. Delivery was
stopped before commit/push, the exact source files were staged, and navigation
was rechecked. No frozen experiment source or output was changed to resolve it.
The source protocols also contain five original Markdown hard-break trailing
spaces flagged by `git diff --check`; those bytes are intentionally preserved
for hash identity. New recovery edits are checked separately from those two
unchanged historical protocol files.
