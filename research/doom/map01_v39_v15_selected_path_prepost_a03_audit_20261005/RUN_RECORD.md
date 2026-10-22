# Run record

Allocation: V39-V15-PREPOST-A03-AUDIT-20261005-01  
Issue: #7933  
Frozen main base: 46b9bc03f6f7dc38ba683c84622df9bab567df77  
Parent candidate: #7926, commit 6bbdc0a705b60c9794805db966889fd65006cd61  
Candidate invocations: 0  
Auditor invocations: 1  
Retries: 0  
Auditor exit: 0

## Runtime and stop evidence

Docker Engine was reachable, but image listing failed because local containerd content-store blobs returned `operation not supported`. Docker execution STOP; no container PASS is claimed. A local temporary package could not be created because the workspace filesystem returned `No space left on device`. The frozen host-Python standard-library fallback was used, feeding the exact committed source and parent input bytes through an in-memory read adapter; the auditor's normal CLI entry point and named input bindings were executed once. No retry occurred.

## Outcome

PASS_AUDIT_V2_LOST_RELEASE_DETECTION_SCOPED: 50/50 baseline checks passed; 7/7 mutation controls rejected; errors empty. The audit independently confirms the synthetic trace's normal empty post-sample and the lost-SPACE case retaining keycode 65, suppressing that key's release classification, and failing terminal cleanup closed. Parent A02 audit remains unchanged and FAIL.

Scope remains fake-X raw instrumentation only. No real X11, physical input, application effect, gameplay, threat efficacy, useful feedback, latency, or recovery-efficacy claim.
