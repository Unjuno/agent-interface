# Retaining a read source through generation reclamation

## Outcome

**PASS_RECLAMATION_HANDLE_BOUNDARY_SCOPED**. One locally frozen formal orchestration,
63/63 completed cases, 126 distinct worker processes with recorded exit 0.
Independent raw-only audit: PASS, zero errors; nine corruption controls rejected.
12 construction unit tests passed. Source and all first outcomes remain unchanged.
GitHub publication: **STOP_GITHUB_WRITE_TOOL_UNAVAILABLE**. No remote successor Issue,
branch, PR, merge or deletion was performed. No remote preregistration is claimed.

This result supports the narrow hypothesis, NOT the safety of every tested policy.
The resolved-path and directory-FD controls separately fail cross-epoch attribution.

## What was changed relative to existing work

#3938's pinned-generation approach explicitly assumes immutable, retained generation
directories and excludes reclamation. We deliberately tested outside that assumption:
old-directory unlink/recreation and replacement of a child data-file entry. We did
not repeat its formal allocation or claim that its scoped result was false.
The initial overlapping epoch/publication plan was stopped before any allocation.
#3937's file-rotation study, #3933 epochs, #3931 crash commits and #3941 concurrent
cursor commits were not modified or rerun. #3876 remains open.

Two exact upstream files were used unchanged: reader.py and DeliveryLedger v2,
verified by both Git object hash and SHA-256 (UPSTREAM.json). The foreground publisher
uses the actual DeliveryLedger.prepare format; it is a finite fixture, NOT an
interactive_v17 or production emitter. Exact read_pending is called by a separate
reader process. Only notification bytes are handled; no model, GUI, OS input or
actuation is involved.

## Results

Seven schedules x three policies x three repetitions = 63 cases.
Each policy has 21 cases, including three deliberate stale-epoch refusals.

| Policy | Delivered responses | Epoch refusals | Source-unavailable refusals | Cross-epoch misattributions |
|---|---:|---:|---:|---:|
| RESOLVED_PATH | 15 | 3 | 3 | **6** |
| DIRECTORY_FD | 12 | 3 | 6 | **3** |
| STREAM_FD | 18 | 3 | 0 | **0** |

Cross-epoch counts are included in delivered counts, not additional cases.
Three repetitions are finite deterministic repetitions, not a reliability estimate.

For the nine reclamation/replacement cases per policy (UNLINK_OLD, RECYCLE_NAME,
REPLACE_FILE), resolved-path returned six B suffixes labelled A and refused three;
directory-FD returned three B suffixes labelled A and refused six; stream-FD returned
the correct A suffix in all nine. Thus safe refusal and delivery continuity are
separate results. The other twelve cases per policy are controls: stable/current
switch with A retained, wrong-epoch-before-prepare, and explicit fresh B adoption.
All policies matched their frozen control expectations.

The old stream FD retained its device/inode/size after unlink/recycle/replace; the
link count was zero in those cases. This is evidence of the live handle's object
retention, NOT a durable producer identity. All reader FD counts returned to their
baseline, including refusals. Raw process stdout framing, requests/responses, ordered
barrier timestamps, filesystem bytes, cursor offsets/digests and no-authority flags
reconciled in the separate audit process.

## Interpretation

A pathname pins a name, not a lifetime. A directory descriptor pins the directory,
not every child entry. In this Linux fixture an already opened stream descriptor
kept the old file readable after its name was unlinked or replaced. Python's Unix
file removal documentation describes retaining storage until the last open handle
closes; the empirical result is limited to our actual interpreter/filesystem stack.
Source: https://docs.python.org/3.13/library/os.html#os.remove

A candidate host retaining historical notification availability could hold the
stream handle until response construction completes, or use an explicit generation
retention lease preventing early reclamation. Only the first was tested here.
Do not infer latest-at-return state, action authority, ACK, exactly-once model
consumption or durability from an old-but-correct response. Do not promote this
research adapter into production based on these tests alone.

## Failure history retained

Construction attempt-01 stopped before publisher readiness and before any scientific
row. Source bytes, raw STOP and driver logs are preserved. Bounded minimal-process
diagnostics isolated an interaction between ordinary site startup and a 256MiB
address-space limit; the exact internal cause was not established. Before freeze,
child startup changed to -I -S -B. Construction attempt-02 completed three excluded
cases and their raw audit; 12 unit tests then passed. Formal invocation count is one;
formal reruns/replacements/source edits are zero. No post-formal auditor repair.

## Limits

Private Linux x86_64 container, CPython 3.13.5; no usable Docker engine/image identity.
No Docker Desktop/OrbStack, other-OS, performance or production equivalence.
Publisher changes occur only at a barrier AFTER all preparation handles are acquired.
No mutation during the multiple preparation opens is tested. No original inode is
modified in place; an FD would not make such writes immutable. No hostile producer,
concurrent append snapshot, high-load FD exhaustion, multi-publisher, process crash,
power-loss durability, model viewing or GUI/task effectiveness claim follows.
The auditor is separately implemented stdlib code by the same research agent; it is
not an external human review or a proof against forged evidence.

## Evidence identifiers

- Base main: b2457b746a6df06f6536585dfe2ab937aff639f4
- Allocation: inbox-reclamation-e58c-20260922-01
- Freeze SHA-256: 217c766e1929c54ad02e6fe47a318130d0bfd568f64d8d079144bc43ef381a75
- Audit SHA-256: 9ff4d8eba551665ebfb26488e257776ef019f8c0586049d176ebff7a7c8bd78a
- Raw set SHA-256: 0dfc745678b9c18088f7f7c5e371cc8061c91b03ce56784dee4048535729502a

The raw-set hash is SHA-256 of UTF-8 json.dumps(AUDIT.json.raw_files_sha256,
sort_keys=True,separators=(',',':')). All 63 original RAW.json files are retained.
Their JSON embeds the original observer file bytes and process transport bytes
losslessly in base64. Ephemeral CURRENT symlinks and redundant mutable working copies
are not required for re-audit and are excluded from the integration patch.

## Integration disposition

All additions stay in research/integration/inbox_reclamation_e58c_v1/. No root README,
shared runtime, workflow, previous evidence or remote ref was changed. The separate
issue/PR drafts are NOT submitted. Before publication, an integration agent must
recheck main, concurrent ownership, path availability and existing source provenance,
then publish the unchanged allocation as retrospective/local-freeze evidence. Never
backdate remote preregistration or rerun this consumed allocation. A new live producer
or model-facing experiment requires its own successor, environment and freeze.
