# Issue #59 A02 — V39/V15 retained trace audit STOP

**Disposition: `STOP_PROTOCOL_INPUT_MISMATCH`.** This was an audit-only successor to [PR #7916](https://github.com/Unjuno/agent-interface/pull/7916). It did not rerun or modify A01. The parent A01 candidate and its original auditor FAIL remain immutable.

## H / T / D / C / U

**H.** A separately implemented raw-only audit should reconstruct the retained A01 timeline while scoping owner-state ordering to the interval before the post-batch keymap sample, and reject six frozen mutations.

**T.** One standard-library auditor invocation on the three pinned A01 files; candidate/runtime invocations 0, retries 0. Auditor source, inputs and protocol were committed before execution. Docker Engine 29.4.0 image inventory failed on a cached content-store blob with `operation not supported`; this JSON-only audit therefore used the single host Python 3.14.5 execution. No runtime or external state was touched.

**Observed result.** The exact raw SHA-256 matched. The raw timeline assertions reported 27/27, and all six in-memory mutations were rejected. However, the invocation wrapper passed A02's own `PRE-RUN.json` instead of the frozen A01 `inputs/a01_PRE-RUN.json`. The auditor correctly emitted `FAIL` with `pre_run_sha256_mismatch`, `pre_run_provenance_mismatch`, and `pre_run_source_binding_incomplete`. The wrapper process exited 0 because it printed the auditor JSON without propagating that internal FAIL; process exit 0 is not a passing audit.

**D.** Frozen pass criteria were not met. Record this first outcome as STOP; no retry, input substitution, code change, or reinterpretation was made. The 27 raw checks and six mutation rejections are preserved as partial diagnostics only, not an independent audit PASS.

**C.** The mismatch is an execution input-binding defect, not evidence against the A01 raw event sequence. Conversely, raw chronology checks do not overcome failed provenance validation.

**U.** A02 does not upgrade the parent A01 audit, verify that source modules were loaded, or qualify full V39 startup, real X11, physical key state, application effect, useful feedback, latency, recovery, threat response, or gameplay. XSync remains server synchronization only. Issue #59's live threat-exposure gate remains open and unassigned.

## Reproduction and custody

- [Frozen protocol](PROTOCOL.md), [PRE-RUN freeze](PRE-RUN.json), and [auditor source](audit_v2.py).
- [Exact first auditor stdout](AUDIT_V2.stdout), [structured STOP](RESULT.json), [run record](RUN_RECORD.md), and [actual/intended input binding](RUN_COMMAND.txt).
- All copied inputs and their hashes are in [SHA256SUMS.txt](SHA256SUMS.txt); original A01 files are also linked in [PR #7916](https://github.com/Unjuno/agent-interface/pull/7916).
- Successor: [Issue #7921](https://github.com/Unjuno/agent-interface/issues/7921).
