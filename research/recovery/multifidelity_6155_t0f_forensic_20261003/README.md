# #6155 T0f forensic custody — not a formal result

**Controlling scientific disposition: STOP_PREREG_SOURCE_HASH_MISMATCH.**
This is a preservation-only capsule for the consumed allocation
`MULTIFIDELITY-6155-T0F-ANYTIME-CPU-20261003-01`. It is not a new allocation,
a runnable restart, an accepted experiment result, or promotion of the
historical exploratory PASS labels.

The original integrity STOP already preserved on main remains unchanged:
[canonical STOP record](../../analysis/multifidelity_control_variate_6155_t0f_integrity_stop_20261003/STOP.md).
The existing question [Issue #6155](https://github.com/Unjuno/agent-interface/issues/6155)
remains unresolved; this custody archive does not close it.

## What is preserved

| Snapshot | Exact source ref | Original files | Archived subtree |
| --- | --- | ---: | --- |
| Frozen preparation | `46cfbcf9ee99c5394f755b3d45cd1c0e6f876f29` | 5 | `freeze_source/` |
| Invalid later local execution and addendum | `724241144be838c1aefe9f027b6b1321af17cb64` | 12 | `invalid_local_run/` |

All 17 source-path entries retain their original Git blob IDs, bytes and file
modes, without normalizing line endings or correcting historical text.
[SOURCE_BLOBS.tsv](SOURCE_BLOBS.tsv) binds each original path and commit to its
archive destination, blob ID, size and SHA-256. The original pathname is
`research/analysis/multifidelity_control_variate_6155_t0_v5_anytime/`;
the archive location separates these invalid records from valid method results.
Both original branch tips are retained as parents of the custody commit, so the
complete original histories and original paths remain recoverable with Git.

## Chronology and contradictory historical labels

The original integrity check stopped before formal candidate/auditor invocation,
with counts 0/0/0 at that boundary. A later local execution nevertheless ran the
candidate and auditor once each against local manifest-matching files, before
the actual frozen GitHub blob bytes had been compared. It did not repair or
fulfill the stopped formal allocation. That later exploratory execution and
its replay are preserved as invalid forensic observations only; retries were 0.

The original author disclosed this sequence in
[the terminal Issue record](https://github.com/Unjuno/agent-interface/issues/6155#issuecomment-5959397918)
and [merged STOP PR #6792](https://github.com/Unjuno/agent-interface/pull/6792).
The preserved [PROVENANCE_STOP.md](invalid_local_run/PROVENANCE_STOP.md) states
the same qualification. Its original `REPORT.md`, `RUN_RECORD.json` and
`raw/audit.json` still contain `PASS_METHOD_SCOPED`; these are superseded
historical local-run labels, **not formal scientific PASS**. Likewise
`FREEZE.json.source_readback_exact=true` is an invalid historical assertion
contradicted by the retained source hashes. None of these fields was silently
rewritten to create agreement.

Four declared source hashes still disagree with their exact Git bytes:
`PROTOCOL.md`, `fixture.json`, `candidate.py` and `audit.py`.
The discrepancy was reported as two bytes per file and consistent with
line-ending drift; its cause is not established by this archive. The committed
files are not proof of the exact local bytes executed.

## Custody checks, not scientific revalidation

A read-only check of original Git blobs verified all 17 entries and reproduced
the four unrepaired source-manifest mismatches. The saved base64 decoded to a
124,003-byte gzip stream (retained SHA-256
`1dc7b66d7b6f7057c263ed5a21364c3d3b7d282603b6934cf9ee8acc9067cb96`);
decompression yielded 3,442,443 bytes and 20,000 syntactically valid JSON rows,
with retained SHA-256
`4a15bf2f83aa3c24e559b2b4876204cd6bdb29f36d9604118036c1316850b21c`.
These are byte-custody observations only. No original candidate, auditor,
corruption control, simulator, model, GUI, container or GPU was invoked.

Original CRLF, trailing whitespace and extra EOF blank lines are retained as
source evidence. Git whitespace diagnostics on the copied historical files are
expected archival diagnostics, not permission to normalize the frozen bytes.
The three new custody documents are checked separately for whitespace errors.

Do not execute the reproduction commands embedded in the historical report,
repair the freeze, replace rows, pool with earlier #6155 results, infer an
audited natural-population/GUI/model benefit, or restart this consumed allocation.
Any future study requires its own reviewed source identity and prospective
allocation. This capsule preserves a failed provenance boundary and the
disclosed invalid output; it creates no scientific result or runtime adoption.
