# Local CI record

The package construction suite passed 5/5 after the pre-freeze test-only fix.
The formal input `FREEZE.sha256` and package-wide `SHA256SUMS` both verify.

The complete test command set listed in `.github/workflows/analysis-index.yml`
was replayed locally, including the index checker, all listed analytical
unittest suites, the new #6645 T1 suite, and `research/analysis/test_check_index.py`.
The workflow's prescribed frozen-source restoration was replayed first; its
restored `analysis-index.yml` matched SHA-256
`b19000e027e7379ef6c0122e3f8cfd0b2faacb4c54d985ab87d27c1be914f7c2`.
Every suite passed in that replay.

An initial broad local attempt omitted the workflow restoration and failed two
geometry provenance tests because the current workflow hash differed from the
historical hash they require. This was a local harness-ordering issue, not a
test or experiment change; the exact CI restoration was then applied and the
full listed command sequence passed. The checked-out workflow was restored to
the current branch version afterward, with only the T1 test step added.
