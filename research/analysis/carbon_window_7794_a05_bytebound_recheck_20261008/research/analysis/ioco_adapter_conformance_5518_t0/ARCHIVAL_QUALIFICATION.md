# Archival qualification — Issue #5518 T0

This packet preserves the original allocation artifacts and later provenance
erratum without editing either. It is a historical execution record, not an
accepted new research result.

## Disposition

The allocation-level status is `STOP_SOURCE_COMMIT_PROVENANCE`; the broad
hypothesis is duplicate/insufficiently novel relative to the already retained
#5518 T0–T7 sequence. The original `audit.json` says
`PASS_T0_IOCO_SYNTHETIC_CONTRACT`, but that label is not promoted here.

`ERRATA-PROVENANCE.md` documents that the raw execution record names source
commit `798efe7ba45e22f393043878c5c600a1980afa4a`, whose committed `audit.py`
is not byte-identical to the frozen/executed auditor. Later Git republishing
and an audit-only validation cannot repair the original run's source pointer.
The finite authored fixture classifications remain provenance, not a novel
scientific PASS. No raw, audit, execution sidecar, or freeze is modified.

## Scope and existing successor

This is a finite synthetic contract only: no actual adapter, GUI, runtime
task-effect, latency, production ABI, or product safety result. The separate
#5518 T7 bounded-quiescence result was preserved through PR #5651 and is not
combined with this T0 allocation. Existing comments say T0–T7 already span
the broad hypothesis; stale-admission and false-success fixtures were not
preregistered as a distinct residual question.

## Preservation validation

The 19 original files are copied byte-for-byte from
`a64f130d2c24999e657d18caa3fc777cc2f94ed5`. This PR adds only this qualification,
a Git attributes rule that preserves exact artifact bytes, and a discovery
entry. No candidate, test suite, auditor, or formal allocation is rerun for
this archive. Any future work needs a non-overlapping question and a new
allocation with source identity frozen before execution.
