# V15 per-key owner identity revalidation A02

**Decision: `FAIL_V15_PERKEY_SELECTED_OWNER_IDENTITY` on candidate head
`4158d9b063e7cbf56828f1b0667ec2714af0ff2b`.** The refreshed startup test
reproduces the #8079 mismatch after the V39 release-safety dependencies were
updated. V15 plus `--per-key-input-measurement` selects the raw current V12
owner (`01c41f5a…`) instead of the archived A01 owner (`b63e8a92…`). The
selected raw owner does match the exact current source manifest; the archived
A01 owner hash is not recorded for that route.

## Question and decision rule

- **H:** On this refreshed PR head, V15's early release-backend import still
  leaves `input_owner_v12` cached, so the combined V15/per-key route selects
  the raw current owner instead of the requested A01 owner.
- **T:** Run the exact V12-per-key, V15-default, and V15-per-key startup
  boundary probes from fresh processes. Replace only optional GUI bindings;
  stop at `suite.Session` after backend selection and source manifest writing.
  Forbid subprocess/thread starts, X display/input calls, session construction,
  and owner instantiation.
- **D:** PASS only if V12-per-key and V15-per-key both select the archived A01
  owner, default V15 selects current V4, all routes reach the boundary, and
  no forbidden call occurs. Any selected owner mismatch is FAIL. Environment
  or guard setup failure is STOP.
- **C:** The later release-batch and InputOwner changes may have changed
  import ordering or class selection relative to #8079's `cceb9d2` source.
- **U:** This tests Python startup identity only. It does not instantiate an
  owner, execute DOWN/UP, test physical release, application consumption,
  threat handling, useful feedback, recovery, ammo/progress, or a terminal
  game result.

## Result

All three route probes exited 0 and reached the guarded boundary with no
session or owner instantiated and no forbidden calls. V12-per-key selected
the archived A01 owner; default V15 selected
`research/live_control/input_transition_owner_v4.py`; combined V15/per-key
selected `research/live_control/input_owner_v12.py`. The independent
PowerShell audit verified all 56 frozen source snapshots and their
materialized copies, stdout/result consistency, owner hashes, boundary flags,
and preservation of the first environment STOP. Audit integrity passes while
the feature gate fails.

The first candidate attempt stopped before the boundary because `openpyxl`
was absent. That STOP remains under `results/current-head-4158-run01/`.
`CONSTRUCTION_REPAIR_01.md` records the inert optional-import stub used for
the separate successful attempt. The first auditor's singleton-array bug and
its repaired readback are also both retained. The replay-materialized source
trees were independently confirmed 56/56 against the frozen manifest, then
pruned as exact duplicates of `source-snapshots/`; see
`MATERIALIZED_SOURCE_CUSTODY.md` and `MATERIALIZED_SOURCE_AUDIT.json`.

## Reproduction and audit

The source tree is materialized from `source-snapshots/` and checked against
`source-manifest.json` by `replay_startup_v2.py`. With Windows Python 3.11.9,
Pillow, and NumPy installed, run from the repository root using a new output
directory:

```powershell
python -B research/doom/v15_perkey_import_59_e0cc_a02_20261005/replay_startup_v2.py research/doom/v15_perkey_import_59_e0cc_a02_20261005/results/reproduction-01
pwsh -NoProfile -File research/doom/v15_perkey_import_59_e0cc_a02_20261005/audit_results_v2.ps1 -RunDirectory results/reproduction-01 -AuditOutput AUDIT_REPRODUCTION_01.json
```

`WSLC_PREFLIGHT.txt` retains the
pinned WSLc dependency stop and host cgroup warning; no candidate ran in
WSLc. `SHA256SUMS.txt` binds the retained package files.

This is a construction FAIL, not a physical-release finding. It does not
authorize or replace the fresh live threat exposure required by Issue #59;
that private game lane remains unassigned. No runtime code was changed.
