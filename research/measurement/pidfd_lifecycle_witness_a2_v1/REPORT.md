# #1631 pidfd lifecycle witness A2 — formal result

Decision: **PASS_PIDFD_LIFECYCLE_WITNESS_A2_SCOPED**.

Fresh successor to #1621; the stopped #1621 invocation is not pooled or rerun. The only A2 factor is outer launch containment: lifecycle cases use fork instead of starting a fresh Python interpreter; all 200 exec cases still perform a real same-process exec.

## First outcome

- lifecycle alive pidfd unsignaled: **1000/1000**
- verified exited pidfd signaled: **1000/1000**
- same numeric PID across exec: **200/200**
- pidfd still unsignaled after exec-ready: **200/200**
- exec target exit signaled: **200/200**
- lifecycle-aware stale authorization rejects after exit: **1000/1000**
- candidate/oracle mismatch: **0**
- copied-result corruption controls: **5/5 reject**
- formal1 / reruns0 / replacements0 / tuning0
- execution: **11.67 s**, max RSS **12,288 KiB**, Python 3.13.5. Timing is descriptive, not a scientific threshold.

## Interpretation

pidfd supports a scoped process-lifecycle witness: the originally opened process object is alive versus exited. It is strictly **not** evidence of same executable/code trust because the same pidfd remains unsignaled across exec. It also cannot identify HUMAN, OS, EXTERNAL_PROCESS, or an exact semantic actor class.

The stale-policy control is contractual: a stored numeric PID remains syntactically present after target exit, while the corresponding pidfd is signaled and therefore permits a lifecycle-aware gate to reject. No forced PID-reuse event is claimed.

## Scope

One Linux container/kernel/Python runtime. No PID-reuse stress, namespaces, pidfd transfer/delegation, HUMAN attribution, security proof, GUI/model/task benefit, latency claim, or production ABI. A useful next integration discriminator would compose pidfd lifecycle with a concrete broker/session scope, while preserving #1600's rule that the witness taxonomy cannot exceed what the trusted source actually distinguishes.
