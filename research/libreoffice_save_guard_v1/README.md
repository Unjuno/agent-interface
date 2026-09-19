# LibreOffice save guard v1

This directory retains the one-factor OS/file-guard successor to Issue #254 / PR #274.

Two consumed allocations:

- `c284-flock-01`: advisory `flock` held after final precheck across Save; result `PERMISSIVE_STALE` because LibreOffice replaced the pathname with a new inode while the lock remained on the old inode.
- `c284-lease-probe-01`: `F_SETLEASE(F_WRLCK)` attempted only after Calc was already open/edited; result `UNAVAILABLE_POST_PRECHECK` with `EAGAIN`. No Save occurred in this rung.

The exact X11/Office input-policy Git blobs are recorded in `SOURCE_PROVENANCE.json`; the branch does not duplicate their historical source trees. `REPORT.md` contains H/T/D/C/U and limits. `AUDIT.json` is a post-outcome independent check; rung-specific frozen auditors are also retained.

Fresh reproduction must use new result directory/allocation names. Do not rerun the retained IDs or rewrite their JSON.

The full curated binary evidence ZIP is conversation-retained and referenced by checksum in `ARTIFACTS.json`; the GitHub tree is intentionally not described as byte-complete raw retention.
