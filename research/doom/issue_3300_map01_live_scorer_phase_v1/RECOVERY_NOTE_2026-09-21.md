# Recovery note — source branch through run56

This integration intentionally imports the additive MAP01 construction record
through run56 from source branch `research/3300-map01-live-scorer-phase-v1`,
commit `0ad6b6784f5f9876d03138c97ae3d79d6129ccd3` (last complete snapshot
before later run commits). The source branch head at review time was
`4f77a79b87c49e5f408207f28069fe9beb1c0a88`.

The source head contains later result directories for runs57, 59, and 60, but
21 tracked files in those directories are one-line `@work/...` references,
not the referenced JSON, Python, or Markdown payloads. The paths do not resolve
inside the repository snapshot. Run57 also has a 960-byte binary and a failed-
attempt binary copy without the missing raw record, manifest, runner, or audit
that would bind them to an experiment; these orphaned files are excluded too.
Therefore those records are not treated as auditable results and no result,
STOP, or failure is reconstructed from their names alone. The source PR/branch
remains available for a later attempt to recover the original payloads. Run58
is not present in the source result-directory inventory and no claim is made
about it.

Checks on the imported snapshot:

- `python3 -m unittest -q`: 27 tests passed across the imported audit modules;
  the core `test_audit` suite contains 17 of these.
- Run53's retained audit has no errors, marks `formal_allocation: false`, and
  its `raw_sha256` matches the committed raw JSON.
- Run54 preflight JSON and run55 comparison JSON parse successfully; their
  accompanying H/T/D/C/U reports retain HOLD dispositions.
- Run56's retained audit reports
  `PASS_BREAKPOINT_TIMESTAMP_CONSTRUCTION_ONLY`, zero errors, 23 samples,
  `formal_allocation: false`, and a raw SHA-256 matching the committed record.
- The four exact scorer/helper files named in run52's invocation retain the
  same Git blob IDs on current main as at the recorded source commit.

These checks do not validate uncommitted payloads referenced by runs57/59/60,
prove breakpoint timestamp accuracy or non-perturbation, or authorize formal
MAP01 collection. Issue #3453 remains HOLD; formal allocation remains 0/120.
