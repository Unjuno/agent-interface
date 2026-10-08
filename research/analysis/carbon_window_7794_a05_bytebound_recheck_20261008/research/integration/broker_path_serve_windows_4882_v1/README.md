# Windows `serve()` path-boundary successor for #4882 — allocation 05

## H / T / D / C / U

**H.** When the #4876 root-confined resolver is wired into a copy of the exact
current-main host broker, native Windows `serve()` accepts canonical in-root
schema/image/working paths (including NTFS junction aliases), while rejecting
external-junction, absolute, traversal, ambiguous and missing paths before the
subprocess boundary. Rejections must leave `authority_granted=false` and return
an explicit path-rejection receipt.

**T.** Allocation `broker-path-serve-windows-4882-20260928-05` is frozen on
main `5670372e20065d3d8286105ed4ea9615952b116f`. A 23-request matrix contains
5 accepts and 18 rejections across schema, image and working fields. Two
directory junctions (one internal, one external) point at durable test content.
The copied candidate broker runs actual `serve()` once per isolated request;
only `subprocess.run` is replaced by an in-process argv recorder. The complete
fixture manifest remains on disk for one separate live filesystem audit before
narrow cleanup. No container is used because the tested request/filesystem
semantics are native Windows NTFS; no model process, CLI, network, GUI or GPU
is invoked.

**D.** `PASS_WINDOWS_SERVE_PATH_BOUNDARY_SCOPED` requires 5 exact canonical
accepted argv calls, 18 authority-free path-rejection receipts with zero mock
calls, 23 unique request/receipt pairs, unchanged fixture inventory, live
junction-target verification, three effective corruption controls and zero
independent audit errors. Any invalid path reaching the recorder is
`FAIL_WINDOWS_PATH_ESCAPE_REMAINS`; fixture/API failure is STOP, not a resolver
result.

**C.** Production broker bytes and the candidate adapter are pinned. Only the
candidate path adapter and its typed path-rejection mapping differ from current
main. The subprocess recorder never launches a process. IPC scratch is removed
file-by-file; after audit, cleanup removes only the two verified junction
entries and leaves the ordinary isolated fixture tree intact.

**U.** This is a candidate-only Windows broker-boundary construction result,
not a production remediation, real host CLI/model call, schema/image file read,
exploitability or race-resistance proof, Linux/macOS parity, #3152 typed-vs-
scalar live transfer, #57 efficiency result, or task-effect claim.

## Frozen sources and preflight

`FREEZE.json` identifies current-main broker blob `5734f54f…`, #4937 candidate
broker lineage, and #4876 resolver blob `cdd0e3d5…`. Fixture-free tests passed
3/3: 5/18/23 matrix, exact resolver AST identity and a broker AST delta limited
to `host_path`, `serve`, plus the policy import. `py_compile` passed. RAW,
manifest and IPC output paths were absent at freeze.

## Allocation 05 result

The runner executed exactly once on 2026-09-28 and returned
`RUN_COMPLETE`: 23/23 rows, five in-process recorder calls, and unchanged
fixture inventory. The separate live auditor returned
`PASS_WINDOWS_SERVE_PATH_BOUNDARY_SCOPED`, 23 rows, `errors=[]`, and all three
corruption controls rejected their mutations. Raw, manifest and audit are
retained under `results/allocation-05/`; the runner was not repeated. The
fixture's two junctions are removed only after audit by the narrow cleanup
script; the ordinary temp fixture tree is intentionally retained.

This supports only the scoped candidate `serve()` path-boundary result in the
scope limits above. Earlier #4882 allocations remain unchanged.
