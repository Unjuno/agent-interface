# Archival qualification — WSLc allocation-10 preparation

Preserves one standalone CPU-only WSLc construction preflight and its raw
receipts. The preflight is separate from the later in-window formal construction
gate. Formal six-worker candidate/CUDA/auditor/retry counts remain 0/0/0/0.
The requested interval elapsed without a coordinator grant; this archive is not
a lease and must not be used to start GPU work.

The first receipt auditor's false-negative and the corrected recheck are both
retained. The corrected scoped PASS validates only the tested source/test
contract and unprivileged writable evidence bind in the recorded WSLc image; it
does not establish six-worker coexistence, GPU performance, resource isolation,
or product benefit. Before any future formal allocation, refresh exact current
main/source hashes and obtain a new explicit exclusive interval. The prior
allocation-09 STOP remains unchanged.

The `FREEZE.json` source SHA-256 values were computed from the Windows/WSLc
CRLF working-tree bytes. This macOS/Linux checkout materializes the same tracked
Git blobs with LF endings, so their raw SHA values differ here. Re-encoding each
of the five frozen source files from LF to CRLF reproduces all five recorded
hashes exactly; the Git blob IDs also match the original branch. This is an
expected line-ending representation difference, not evidence of changed source
content. Do not normalize the retained source bytes to disguise that distinction.
