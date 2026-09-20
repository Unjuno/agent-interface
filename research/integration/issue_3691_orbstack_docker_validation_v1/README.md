# Issue #3691 exact-source OrbStack validation

## Preregistered H/T/D/C/U

- **H:** The exact strict auditor and regression suite in PR #3697 passes its
  unit suite and canonical CLI inside pinned, network-disabled containers.
- **T:** One fresh container runs the frozen eight-method unittest suite. A
  second fresh container invokes the raw-only CLI against exact original raw,
  predecessor freeze, study manifest and the separately pinned study digest.
- **D:** PASS requires eight tests, exact source/input hashes, CLI exit 0 and
  `PASS_OFFLINE_STRUCTURAL_AUDIT`, no errors, all 12 current-source mutation
  controls rejected, and unchanged frozen inputs. Any gate failure is FAIL or
  STOP as defined in `PREREG.json`.
- **C:** OrbStack Docker Engine 29.4.0, Linux/arm64; pinned Python base; runtime
  network disabled, read-only root and candidate-source mount, bounded `/tmp`,
  separate output mounts. No X11, GUI, input, model or predecessor XRes rerun.
- **U:** Finite adversarial offline audit checks only. No claim of arbitrary
  auditor completeness or broader XRes/runtime safety.

## Exact frozen target

Candidate source is PR #3697 commit
`f823cbc77e87d2f9ff3456ddf49f2f819bbc340a`, folder
`research/issue_3691_audit_integrity_v1/`. The file digests, main base commit,
engine, image, invocation counts and decision gates are frozen in
`PREREG.json` before either container run. The candidate worktree is mounted
read-only; outputs are written to this separate evidence branch/path.

The prior Docker Desktop STOP and its native construction outcomes remain
unchanged in PR #3697. This is a distinct OrbStack allocation, not a relabeling
or retry of those outcomes.

Before execution, a read-only byte check found the historical
`artifacts/native_audit.json` contains 11 control keys while the frozen current
`audit.py` defines 12. The old receipt is preserved. The fresh CLI output will
report the current source's actual controls, and the discrepancy will be
recorded rather than silently reconciling the old result.

## Allocation 01 result

**`PASS_ISSUE3691_CONTAINER_VALIDATION_SCOPED`** for the exact frozen PR #3697
snapshot. The first fresh container ran all 8 unittest methods: 8/8 passed.
The second fresh container ran the canonical CLI once and returned
`PASS_OFFLINE_STRUCTURAL_AUDIT`, exit 0, `errors=[]`; all 12 controls defined
by the current auditor were true. Captured stdout and `--output` JSON are
byte-identical (SHA-256
`cbc8060908aa9af371031b197febf90d7851e12223de9d5a43444f9bfa3579cc`).

The older committed `artifacts/native_audit.json` remains unchanged at 11
control keys and SHA-256
`36e1e9c64c83be35eef3447d76d78d2f62adff257612184beef4162c5e1fb32a`. The
current source defines and emits 12 controls, including
`replacement_study_manifest`. Thus the new exact-source result passes its
frozen gate while exposing a historical receipt/source-generation mismatch;
do not rewrite the earlier receipt or claim it contained the twelfth control.

Unit transcript SHA-256:
`4fdafde3a3a87069472e5a5aa400fcf46260571ba63be7c8f16394678c0f8eb6`.
Full outcome and container/cleanup receipts are in `RESULT.json` and
`RUNLOG.md`; all bundle hashes are in `SHA256SUMS`.

This validates only the finite offline audit suite and canonical CLI for the
exact PR #3697 source commit. It does not prove arbitrary auditor completeness,
revalidate XRes behavior, or integrate the candidate implementation itself.
