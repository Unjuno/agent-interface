# PR #10218 supersession audit

- Audited main: `897f4896d23dd127a4523dc4955e573dace7d674`
- PR #10218 head/base: `b1e24401ca0817ed4504b62f9c7190a0c900735a` / `78cef41de52911b47857d6a62326a0aeb2c91081`
- PR changed paths: 41
- Exact blob comparison: 37 identical, 4 different.
- Main already contains the App Server late-usage implementation and its retained evidence; the PR-only `.gitattributes` line count is zero. All four implementation modules, four adapters/recorder files, and three related test modules are identical; the remaining test-file diff is the obsolete one-second fake-host timeout/cleanup pattern that main repaired in PR #10365.
- Other differing paths: main README contains 13 lines of later effect-attribution evidence absent from the PR; `commands.txt` differs only by the restored CR byte. No unique executable or research evidence would be gained by merging the old branch.
- PR #10218 was closed as superseded on 2026-11-20 21:41 UTC; its source branch remains on origin. The close comment is GitHub issue-comment 7051294171.

This disposition closes only the redundant PR. Issue #57 remains open for real provider lifecycle accounting, caller task success, repeated recovery reliability, and matched efficiency. The remaining full-suite Calc/Fake X failures are preserved and unresolved.

See `raw/path-blob-comparison.tsv`, `raw/remaining-path-diff.patch`, and `raw/attribute-line-audit.txt`; `SHA256SUMS` covers those observations and the frozen conditions.
