# Post-freeze parent synchronization

The A02 source archive was frozen at PR #7662 head `719ef679c977a925db3a6d1fe15f9cd93cf2b42c`, where its manifest covered 18 files. The parent branch later appended six parent-sync/test receipts and `run_current_parent_projection.py` to that directory and updated its `SHA256SUMS`. Those seven files were added after A02 and are not part of the A02 experiment input or result.

`audit_provenance.py` now checks the original `SHA256SUMS` and 18 member blobs directly from the frozen Git commit, verifies those same original member hashes in the current checkout, then separately verifies the current 25-file inventory and exact seven-file append set. The unchanged `audit_readonly_v2.py` can audit either the original 18-file archive or the current 25-file archive; its counts describe the archive passed to it. A02 remains the result from the original 18-file tree.

The post-sync checks are recorded in `PARENT_SYNC_PROVENANCE.json`. They are provenance verification only: no A01 experiment or model/game/input run was repeated.
