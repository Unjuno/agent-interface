# Recovery review: Issue #3892 audit-only snapshot

This directory preserves the exact seven-file source/freeze snapshot from
`research/issue-3892-full-covariate-audit-20260921` at branch tip
`f82d678e10186166490050300a5928ad4c7798fe`. The source files were copied
byte-for-byte; no audit or model process was rerun.

## Outcome boundary

Issue [#3892](https://github.com/Unjuno/agent-interface/issues/3892) records
one formal audit invocation, no model-runner invocation, and the disposition
`STOP / auditor overconstraint`. It reports three
`shift_changed_nonposition_covariate` errors and gives the claimed output path
`audit/formal-01/AUDIT.json` with SHA-256
`5f097558d9f0521d19b6c04842fa89d03944e507e32f3533c51b21c59bffef1d`.
That output file is **not present** in the recovered branch snapshot, so its
bytes and hash cannot be independently verified from this package. The issue
body is retained as the provenance for the reported outcome; this file does
not reconstruct or certify the missing output.

The failed auditor imposed an unpreregistered cross-suite equality condition
on velocity and confidence even though the frozen treatment changes those
features. Therefore its three errors are not evidence of a model failure or
of a six-feature mismatch. Do not treat this STOP as an audit PASS or revise
it post hoc. The corrected successors #3899/#3906, including merged PR
#3913, remain separate and unchanged.

## Scope and validation

The frozen work was a posthoc evidence audit of retained synthetic data only:
no training, inference, GPU, GUI, external network, or model runner. The
original FREEZE specifies cached `needle-pilot05:local` image ID
`sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`
on linux/amd64. This recovery does not claim that image was available or used
for the recovered copy. The current OrbStack host does not have that image
cached, and the freeze prohibits pulling it. A local construction-test attempt
with Python 3.14.5 therefore stopped at import because `torch` is not installed;
this is an environment/setup STOP, not a test result about the frozen auditor.
No formal audit was invoked.

This is an archival preservation of a superseded audit attempt, not a new
formal result and not a promotion of the original model FAIL/STOP. Keep all
later successor results at their existing paths.
