# Browser review transport archive

Original remote `evidence/6914-diff-01a0ff58-20261003`, tip
`ea62e29074f8d65d134f9767b07c527c19d080af`. Preserve all four review-transport
files unchanged. The author's historical "never proposed for main" transport-only
purpose remains recorded; this later user-authorized rescue is archival only.
Original experiment packet was separately rescued via PR #7124.

Checks bind all four original Git blobs, the 408199-byte retained patch and the
canonical changed-blob JSON to their original SHA256 pins. Applying the patch
without executing any postimage into a new exclusive private Git index must yield
exactly all 61 original modes/OIDs. Each postimage's size/SHA256 and original
experiment source/main blob are compared. The shared worktree index is not used.
`--whitespace=nowarn` retains native stream formatting; exact postimage equality
remains mandatory, not a whitespace-normalization acceptance criterion.

This proves public Git-byte transport conservation, not author-private capture
chronology, original Git-version attribution, compression root cause, review vote,
current scientific approval, live browser/SQLite rerun or native effect. No original
producer, historical allocation or review helper is executed.

```sh
python3 -m unittest discover -s runtime/results/browser_transport_rescue_ea62e29 -p 'test_*.py' -v
```
