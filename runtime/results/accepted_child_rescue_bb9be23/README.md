# Accepted-child retained-evidence verification

Source: `research/review-accepted-child-6919-7772-20261003`, commit
`bb9be23e4b8f5eac15812b32f9dd941925cf97de`.
The original 261-file packet is already present byte-for-byte on main (tree
`d206cd5641768e531cb676e278f161d09fe13031`). This successor adds independent
verification, not a second experimental run or a replacement historical verdict.

## Local checks (2026-10-04)

- `python test_archive.py -v`: 2 tests passed on Python 3.14.5 and 3.12.14.
  Each run checks normal and optimized Python reconstruction.
- All 261 original Git blobs, the 253-entry first manifest, the 260-entry
  publication repair manifest, ten Git-bound source images, and frozen audit
  hashes match. Eight retained corrupted-input controls are refused with their
  recorded diagnostics.
- Current-main relay tests: `node --test --test-name-pattern='wrong response identity|invalid reply JSON|occupied original reply|failed reply journal|healthy reply journal|reply reader' runtime/host_v1/test_relay_client.mjs`:
  9 passed, zero skipped/cancelled. These inert regressions cover later journal
  and reader repairs; they do not rerun the historical Windows experiment.

## Evidence boundary

The original first audit still refuses with `peer alive at fault barrier` and
exit 1: `FAIL_PREDECLARED_BASELINE_SURVIVAL`. Baseline peer termination cause
remains `UNKNOWN`. The descriptive V2 audit reconstructs eight retained rows,
not a retroactive PASS of the frozen premise. The historical wrong-ID exit
journal gap remains recorded even though later main includes journal fixes.
Synthetic downstream effects are not physical, GUI, model, or live SDK proof.
Neither owner/peer/collector producers nor historical executable entrypoints
are rerun. Container execution is unavailable because the local image store
returns `operation not supported`; no shared daemon reset or cache deletion
was attempted. Original failures, publication repair, and custody limits are
preserved. Parent #57 and original delivery #6919 are not closed by this rescue.

The source ref may be retired only after main contains this verification,
the original source has a remote archive tag, and fresh exact-SHA and dependency
checks establish that retirement cannot discard new work.
