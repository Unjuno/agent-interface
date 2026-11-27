# Checksum custody correction

The first post-merge Windows verification found three current-worktree checksum mismatches caused by line-ending differences. A follow-up archive audit showed the underlying manifest had been generated from Windows worktree bytes for many historical text files, while Git stores their LF-normalized blobs.

The packet is now marked `-text` so future checkouts preserve committed blob bytes. All 471 manifest entries were recomputed from the exact Git blob bytes, not the current worktree representation. Experiment content and raw observations are unchanged; only manifest values and this custody note changed.
