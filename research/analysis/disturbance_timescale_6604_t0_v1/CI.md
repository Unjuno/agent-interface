# Local CI record

## Current-main validation after rebase

Validated 2026-10-02 on branch `research/disturbance-timescale-6604-t0-orbstack-20261002`, rebased onto main `a2f157397adcfdf490d010707a6a413c9a8c0562`.

- Exact current Analysis Index workflow sequence: **76 tests PASS across 13 suites**. This includes the #6590 geometry-feasibility suite (10 tests), #6617 (7), and #6604 (11).
- `research/analysis/check_index.py`: **PASS**, 481 retained result/failure directories indexed.
- `.github/check_public_navigation.py`: **PASS**, 26 documents / 1,421 repository-relative links.
- `research/check_workspace_index.py --git-tree`: **PASS**, 156 top-level directories reachable.
- The Actions workflow restores frozen workflow source `e2e434dd07e1034c5c4303982a0b1ec33ea35cfd` before tests; this local run reproduced that setup and verified its pinned SHA-256. The restored file was returned to the branch version afterward.
- Initial local attempts exposed two setup mismatches: the sparse checkout lacked 12 directories already retained in main's generated analysis index, and two suites require the workflow's declared working directory/frozen-workflow setup. The directories were materialized locally without changing the generated index; the full exact sequence then passed. These were local harness setup issues, not source or experiment failures.
- The first direct hash-check command was GNU-specific and unavailable on macOS; the same frozen-source digest was verified with `shasum -a 256`.

The formal isolated OrbStack allocation is separate from host-local construction/CI checks. See `formal_02/REPORT.md` and `formal_02/RUN_RECORD.json`; no real GUI/DOOM efficacy or product-level benefit is claimed.
