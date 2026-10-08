# Recovery status — Issue #5084 larger-rung lifecycle package

This directory preserves the exact source package from remote branch
`research/needle-role-skill-lifecycle-4916-larger-rung-v2-20260928` as an
additive recovery. The original branch and files are not modified.

## Evidence boundary

- Issue #5084 records that allocations -01/-02 were not executed and directs
  workers not to launch them. The recorded preflight identified a freeze/path
  mismatch: the v2 freeze accompanies v1 entrypoints that expect a v1 freeze;
  allocation constants also remain -01. The required OrbStack/macOS bind path
  was unavailable on the reporting host.
- No container, model, training, or timing invocation is evidenced for this
  candidate. This archive therefore makes no experimental or performance
  claim and does not authorize a rerun.
- `FREEZE.json` is preserved byte-for-byte. Its `invocations` fields are not
  interpreted here as proof of execution; the discrepancy with the Issue's
  preflight account remains unresolved.
- No proposed allocation was rerun as part of this recovery.

The five source files under the sibling `..._v1/` directory and this package's
`FREEZE.json` and `README.md` are exact copies from the source branch. This
status file and the analysis index entry are recovery metadata only.
