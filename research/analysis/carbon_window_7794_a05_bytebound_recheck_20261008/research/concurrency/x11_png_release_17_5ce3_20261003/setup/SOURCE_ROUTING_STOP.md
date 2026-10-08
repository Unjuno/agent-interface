The first setup command referenced the preceding study's capture.py in the
worktree after changing sparse-checkout. That file was not materialized, so
Python exited 2 before any Docker build or scientific execution. Its immutable
Git/main record is intact. The helper was copied byte-for-byte from the same
main Git blob into this new additive package; setup uses that self-contained
path. No old producer/output/VM container was rerun or rewritten.
