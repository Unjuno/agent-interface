# Local integration checks and limitations

One-shot formal results remain untouched. Final integration checks are reads,
hashes, and pure fixture tests only; no formal modelchecker/auditor is repeated.

The original index insertion was locally too late (after verifier_*). The
first check_index.py printed `duplicated or unsorted`; its nonzero status was
masked by the following successful git diff check in the same shell command.
Main treated the diagnostic as failure, stopped publication, and corrected the
insertion before verifier_*. A separate remote in-memory insertion had an
off-by-one name extraction and was never sent; it was corrected using an
anchored path regex, sortedness/uniqueness checks and exact deletion reversal.
One attempted combined apply_patch failed context verification and changed no
file; a correctly scoped patch then applied. None consumes a formal allocation.

The remote index payload is fresh main text plus exactly one generated entry,
not the local sparse checkout's older entire index. Deleting the added line
must recover the fetched base byte-for-byte; all existing entries remain.
Sparse local index checks are not full repository index completeness evidence.
Applicable remote CI and reviewed head must be checked before merging.

Initial 53-target manifest and every package file's strict UTF-8 byte roundtrip
passed. This narrative/review completion adds a file and changes review metadata,
so the final manifest is regenerated before complete coverage verification.
Manifest excludes itself only. Frozen sources, first streams and receipts do
not change. Exact package subtree readback is required before ref/PR publication.

Git transport is not retried through the old incomplete promisor history.
Prior #6997 guarded pushes failed on a missing historical object; A01 publication
uses a scoped GitHub MCP tree on fresh main with only this directory and one
index line, preserving reviewed exact UTF-8/CRLF bytes. No lazy-fetch broad
hydration, force push, direct-main rewrite, or old evidence replay is used.
