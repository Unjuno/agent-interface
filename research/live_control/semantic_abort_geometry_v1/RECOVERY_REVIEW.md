# Recovery review: Issue #3943 geometry-abort allocation

The six files under `source/` are restored from the original remote branch
`research/semantic-abort-geometry-20260922-v1` at
`34f3ef8133dfea8552df10c0435bb579ea87d875`. The branch contains the frozen
experiment sources, but not the formal raw bundle, runner receipt, or reported
stdout files. A bounded local search found no saved Issue #3943 output bundle.

## Formal outcome boundary

Issue [#3943](https://github.com/Unjuno/agent-interface/issues/3943),
comment [5766391128](https://github.com/Unjuno/agent-interface/issues/3943#issuecomment-5766391128),
reports one completed 30-case native allocation, an independent raw-only audit
with zero errors, and ten rejected corruption controls. The reported audit
disposition is `PASS_ABORT_GEOMETRY_BOUNDARY_SCOPED`; the overall experiment
disposition is **`HOLD_ORCHESTRATION_EXIT_UNRECORDED`** because the outer
runner exit receipt and `ORCHESTRATION.json` were not captured. The raw audit
hash is reported as
`401a84cb4d9a0fbf53add53a8362a06a629fa2887128ee517245b090d2097135`; formal
stdout and post-timeout observation hashes are also listed in that Issue
comment. Those files are absent here, so the hashes and audit cannot be
independently checked from this repository. Do not upgrade the scoped audit
PASS into an overall PASS.

The Issue reports a finite native-toolkit counterexample: cached move-out
committed in all six relocated cases; refreshing geometry avoided the
before-refresh change but not the after-refresh change (three commits). This
does not establish cancellation safety or model transfer. The earlier
construction failures and the successful ten-case construction-04 are also
preserved in the Issue comments; construction is not the formal allocation.

## Recovery checks and limits

No formal run, rerun, replacement, or tuning was performed during this
recovery. The consumed allocation must not be repeated to reconstruct missing
outputs. The source freeze remains distinct from the invalid compressed
staging attempts documented by the worker. This record and the Issue comments
are not a substitute for the missing raw evidence, runner-exit receipt, or
overall completion proof. Issue #2197 and production integration remain open.
