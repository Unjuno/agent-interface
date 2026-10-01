# #3985 / PR #4012: exact source-and-summary preservation

## Read this before using the historical files

**Disposition remains `HOLD_FULL_RAW_PUBLICATION`.** This directory preserves
the 15 exact Git blobs available at original PR #4012 head
`801df479c7e0ac0f657f5eeb0a29a739ced69363`. They total 56,963 bytes and comprise
source, a frozen plan/environment, historical result/audit summaries and
publication records. This is useful, incomplete historical material. It is not
the complete experiment or a repository-only reproduction of its result.

The original README, PLAN, FREEZE, AUDIT and publication statements are kept
byte-for-byte. Their time-relative wording describes the original publication
attempt; this separate note supplies the preservation boundary. In particular,
`FREEZE.json`'s `formal_started: false` records the preformal freeze. It does not
make the subsequently consumed allocation available to run again.

## Provenance and ownership

- Canonical owner and recovery tracker: [Issue #3985](https://github.com/Unjuno/agent-interface/issues/3985)
- Original delivery PR: [#4012](https://github.com/Unjuno/agent-interface/pull/4012), open Draft at the inspection below
- Original branch: `research/passive-reader-pagination-cost-20260922`
- Experimental base: `b2457b746a6df06f6536585dfe2ab937aff639f4`
- Consumed allocation: `pagination-cost-3985-20260922-01`
- Exact 15-file source tree: `e16672ea6d607c7353fe0581a2363852b455d9a9`
- [Preformal freeze](https://github.com/Unjuno/agent-interface/issues/3985#issuecomment-5766570106),
  [first outcome](https://github.com/Unjuno/agent-interface/issues/3985#issuecomment-5766607302),
  and [original publication checkpoint](https://github.com/Unjuno/agent-interface/issues/3985#issuecomment-5766865126)

This preservation does not take over the raw-publication owner, create another
experimental allocation or successor tracker, lift the original delivery HOLD,
authorize merging/closing #4012, close #3985, or authorize branch deletion.
Keep the original Draft and branch. The [reopening explanation](https://github.com/Unjuno/agent-interface/issues/3985#issuecomment-5859785414)
states why closing the delivery tracker before exact-raw recovery was premature.

## What remains missing

The original archive is declared as
`agent-interface-3985-pagination-full-evidence.tar.xz`, 361,208 bytes, SHA-256
`7bcbeb0b199444c1c5ef38095c3f27fdf19f38a930b8212765f83a8b2a31cfb4`.
The historical record says it contains 196 files, including a manifest with 195
entries. Its identity is recorded here; the archive bytes are not supplied here.

There is no `formal-01/` tree in this preserved 15-file package. Five dependencies
named by the exact FREEZE are also absent:

- `CONSTRUCTION_AUDIT_FINAL.json`
- `construction-01.stderr`
- `construction-01.stdout`
- `construction-01/RAW.json`
- `construction-01/stream.jsonl`

The original raw-only auditor reads those frozen dependencies and each formal
batch's complete inputs, responses, process journals and receipts. `AUDIT.json`,
`AUDIT_EXECUTION.json` and `ARCHIVE_REAUDIT.json` are historical audit records;
copying them does not perform or independently establish that audit here.
All 12 digests in `PUBLICATION.json`'s `published_original_files` match these
preserved bytes; all eight available FREEZE dependencies match. The five missing
dependencies are kept missing, not synthesized or silently removed from FREEZE.

The [September 30 recovery update](https://github.com/Unjuno/agent-interface/issues/3985#issuecomment-5911794508)
reports no retrievable attachment URL or original candidate in its bounded
workspace search. That report is not proof of absence from all other locations.
No new archive-recovery search or scientific execution is claimed by this note.

## What can and cannot be reused

The finite work derivation, exact reader/ledger, harness and decision rules,
measurement-endpoint qualifications and original failure-to-publish boundary are
available for inspection. Preserve the reported scientific decisions
`PASS_PAGINATION_WORK_LAW_SCOPED` and `PASS_LOCAL_BATCHING_TIME_SCOPED` as historical
first outcomes. This preservation does not independently validate their raw
support or replace them with a new scientific FAIL.

The result concerns a warm, already-available local backlog and explicit page
settings. The reader default was already `max_records=32`. The timing includes
loop/cursor handling, clocks and in-memory response retention; it is not an
improvement to the default implementation, disk throughput, live batching delay,
model/GUI/task success, or production acceptance.

## Existing related coverage, checked without rerunning anything

At inspected main `d7eac8608479d1461d3de3bd9cbd8305e28e860d` on 2026-10-01 UTC,
this exact study directory was absent. An untruncated recursive check of
`research/integration`, `research/analysis`, `research/archive`,
`research/archives` and `research/retention` found none of its 13 study-specific
blob IDs. The two exact upstream source blobs already appear in other studies;
they are retained here too because the original frozen capsule uses these paths.
This is a bounded coverage check, not a claim about every compressed archive,
every branch or workers' unpushed files.

Related work already on the inspected main remains separate:

- [#3988 backlog batching](../passive_reader_batch_cost_v1/REPORT.md) has its own
  27-process allocation, CPU/first-return endpoints and 106-file archive. Its
  empty-tail control is outside its timed/accounted drain; #3985 includes a final
  empty check. The two accounting conventions and observations must not be pooled.
- [#4068 / merged PR #4074](../snapshot_demand_index_v1/README.md) retains its own
  103-file demand-index study. It explicitly says the older #3985/#4012 full
  archives are not included; shared comparator source does not discharge this HOLD.
- [#4122 index density](../snapshot_index_density_c5d2_v1/PUBLICATION_NOTE.md)
  retains a separate 66-file memory study and a preformal duplicate-lane STOP.
  It is not replacement raw for #3985.

## Canonical next work and no-duplicate-work rule

Continue the existing recovery thread on #3985 / #4012 only when the original
archive bytes become available. Verify exact size and SHA-256, publish the full
original corpus durably, then obtain an explicitly scoped repository-only audit
and review before changing the original delivery disposition. A checksummed
summary or another study's successful audit cannot meet this gate.

Do not rerun `study.py`, `batch.py` or `supervise.py` with the consumed allocation,
invent a replacement archive, normalize the historical blobs, merge the stale
whole branch, or delete the branch. Any independent new experiment needs its own
ownership and scientific authorization; this archive reserves no runtime slot.

Preservation verification was limited to Git blob identity, byte size, SHA-256,
source-tree reconstruction, frozen/publication digest comparisons and a scoped
index diff. No retained code, tests, auditor, model, GUI, container or formal
experiment was executed for this preservation. No repository CI PASS is claimed.
