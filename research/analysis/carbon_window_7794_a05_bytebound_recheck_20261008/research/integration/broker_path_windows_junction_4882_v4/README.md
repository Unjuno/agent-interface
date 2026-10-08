# Native Windows junction parity successor for #4882 — allocation 04

## H / T / D / C / U

**H.** The pinned #4876 candidate resolver maps a junction targeting a
directory inside the repo to its canonical in-root file and rejects a
junction to an external sibling before returning a host path.

**T.** One fresh allocation, `broker-path-windows-junction-4882-20260928-04`,
is frozen against main `ceda253410ce738571580a5980a4e26dc1c3352a`. It uses
native Windows 11/NTFS and CPython 3.12.10. The candidate function AST matches
the exact #4876 blob in `FREEZE.json`. A fixture-free unit test first validates
the serialized mount-point buffer. The one runner then creates a unique temp
fixture, installs two junctions with the documented mount-point
`FSCTL_SET_REPARSE_POINT` control, and evaluates nine frozen path cases. A
separate auditor inspects live junction tags/targets and row containment before
cleanup. No network, Docker, model, broker, or host CLI runs.

**D.** PASS requires all nine expected outcomes, exact canonical target
identities, verified live junctions, no accepted path outside repo, matching
source/raw hashes, and zero independent audit errors. Any external target
returned is `FAIL_WINDOWS_JUNCTION_ESCAPE`. API/permission/setup failure is a
retained STOP, not resolver evidence. Ambiguous audit evidence is HOLD.

**C.** Resolver code and case intent are pinned; only fixture construction
differs from earlier Windows STOP allocations. The reparse-point setter only
receives two newly created empty directories beneath one unique temp root.
Fixture cleanup is limited to the verified junction entries after audit; no
recursive deletion is used.

**U.** This is candidate-only, one Windows/NTFS host. It does not establish
production remediation, race resistance, actual broker file reads, other OS
parity, or model escalation in #3152.

## Fixture-free preflight

`python -B -m unittest -v test_reparse_payload.py` passed 1/1. It validates
mount-point tag, data length, substitute/print offsets, UTF-16LE lengths and
terminators without creating a file, link, or API handle. Exact sources and
hashes are in `FREEZE.json`. The Microsoft protocol/API references are linked
there as well.

Allocation 04 result and cleanup receipt will be appended under
`results/allocation-04/`; earlier STOP records remain immutable.

## Allocation 04 result

The one native runner completed with 9/9 rows. Both fixture junctions were
created by `FSCTL_SET_REPARSE_POINT`; the independent auditor returned
`PASS_WINDOWS_JUNCTION_CONFINEMENT_SCOPED` with 9 rows and `errors=[]`. It
verified both live junction target identities before cleanup, canonical
in-root results for the root aliases, regular file and internal junction,
rejections for external junction and traversal/absolute-path controls, and
`FileNotFoundError` for the missing path. The external junction did not produce
an accepted host path. This is a scoped candidate result, not production broker
evidence.

Cleanup removed only the two exact junction entries after the audit. The
surrounding isolated temp fixture directories/files remain; no recursive
deletion was used. Exact outcome and hashes are in `results/allocation-04/`.
