# Checkout line-ending custody note

After the formal run, the evidence was cherry-picked onto a clean branch from
current `main`. This Windows checkout has `core.autocrlf=true`, and the package
did not yet have a local line-ending rule. The working copies of text files
therefore appeared as CRLF even though their Git blobs remained LF. The frozen
source hashes were independently verified against those Git blobs and matched
6/6. The candidate and auditor were not rerun.

This follow-up adds a package-local LF rule so Windows and Linux checkouts
preserve the same bytes, restores the working copies to the already-frozen LF
bytes, and rebuilds `SHA256SUMS` from the retained Git-tree-equivalent files.
The formal outputs, freeze, candidate, and auditor are unchanged. The prior
incorrect worktree-derived manifest is superseded by the corrected manifest in
this commit; its original bytes remain visible in the preceding commit.
