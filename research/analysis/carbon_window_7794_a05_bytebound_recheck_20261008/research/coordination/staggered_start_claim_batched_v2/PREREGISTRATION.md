# Issue #3963: immutable-batch supervision successor

Predecessor #3946 remains STOP_EXTERNAL_EXECUTION_ENVELOPE, 38/54 completed
rows plus one partial case. It is not resumed, pooled or overwritten. Interactive
terminal preflight failed with StreamingExecNotEnabledContainerError; no
experiment was invoked by that preflight.

H/T/D/C/U and all nine scientific scenarios, three repetitions, two protocols,
worker/case/auditor/corruption code are unchanged from the v1 preregistration.
Only allocation identity and supervision/serialization change. The original
worker.py, run.py, audit.py and test_audit.py are copied byte-identically.

Fresh allocation: staggered-start-claim-batched-20260922-01.
New path: research/coordination/staggered_start_claim_batched_v2/.
Execution: provided Linux x86_64 container, Python3.13.5, SQLite3.46.1;
no Docker or network-namespace equivalence. No model, GUI, network calls or
external effects. Private database rows and worker processes only.

## Fixed plan

One allocation, nine serial batch invocations, index0..8, six fresh cases each.
One scenario per batch, in v1 order; three repetitions, same alternating arm
order. Every batch first claims a consumed marker with exclusive creation and
an allocation-local file lock. A consumed/incomplete batch is terminal STOP.
Every prior prefix count/hash and receipt is validated before further execution.
Rows are fsynced immediately. No case/batch replacement or rerun. Final receipt
requires all54 rows, nine consumed markers, nine terminal prefix receipts.
Run each frozen command exactly once (i=0,1,2,3,4,5,6,7,8, in order):

    /opt/pyvenv/bin/python /mnt/data/issue3946/batched-study/batch_driver.py --index i

Source hashes are verified before/after each batch. Batch0 cannot reuse an
existing allocation directory. Same54-case gates: baseline39 starts/21 unsafe/
0 refused/36 private effects/39 workers; candidate18 starts/0 unsafe/21 refused/
15 effects/39 workers. Three candidate killed-before-work cases retain an
unresolved claim with no effect and refuse replay. Different-resource workers
must overlap as ACTIVE before either work command. No speedup or physical CPU
parallelism claim. Start admission is not task completion or a perpetual lease.

Require raw-only audit, twelve semantic corruption controls, independent batch
prefix/allocation/source-path/clock audit and four batch-corruption controls.
Eight prefix-guard construction checks passed with no worker invocation.
Reuse old18-case construction only as excluded source validation, not formal.

PASS_PROCESS_START_CLAIM_BOUNDARY_SCOPED supports only this admission boundary;
FAIL_PRECHECK_ADMISSION_POLICY is separately retained. Missing/incomplete
batches are STOP/scientific NONE. No post-freeze source/gate tuning. Preserve all
failures. Batch pauses can change scheduling, so timing is diagnostic only.
No post-admission freshness, automatic claim takeover, external exactly-once,
natural held-out trace, model utility, GUI, cross-platform or production claim.

Roadmap: retain old STOP -> freeze wrapper/provenance -> nine immutable batches
-> independent raw and batch audits -> corruption controls -> additive PR and
main readback -> own-branch cleanup only if safe/supported. Broad parent issues
#3158/#3199/#3209 and the repository roadmap remain open.
