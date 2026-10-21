# Issue #8610 T0 A01 — common-cause degradation contracts

**Internal frozen-fixture result:** `PASS`; independent audit integrity: `PASS`.  
**Issue-level disposition:** `HOLD_PROTOCOL_ARM_MISMATCH` — this run does not validate #8610's stated hypothesis.

The frozen candidate and separate auditor each ran once on the Windows host (CPython 3.12.10), with zero retries and no Docker/WSLc commands. Candidate stdout was transferred directly in memory to the independent auditor's stdin; no output files or temporary files were written. Formal stdout hashes and the case-level outcome summary are preserved in [RUN.json](RUN.json) and [candidate_summary.json](candidate_summary.json).

## What the frozen fixture established

Within its own three-arm fixture, the dependency-aware contract retained 11 supported operation outcomes unavailable under strict binary all-route gating. The auditor independently reconstructed all nine scenarios, detected all three deliberately unsafe raw-to-semantic substitutions, recorded zero authority inflation and false effect claims, and counted mandatory release obligations in 9/9 cases. No dispatch operation was present or executed. Six semantic output mutations were rejected in the pre-formal in-memory construction suite.

These are internally auditable fixture results only. In particular, 9/9 counts retained obligation labels; it is not evidence that release was operationally performed.

## Post-run protocol reconciliation

Issue #8610 specifies a comparison of (1) an independence-assuming component lookup, (2) a dependency-aware contract evaluator, and (3) a fail-closed unknown-dependency control. A01 instead froze and ran (1) strict binary all-route gating, (2) the dependency-aware contract, and (3) an intentionally unsafe silent raw-to-semantic substitution.

Therefore two required policy arms were absent. The auditor PASS applies only to A01's own frozen fixture and cannot substitute for the missing comparison. The issue-level hypothesis and decision criterion were not tested; do not promote A01 as a #8610 method PASS. This mismatch was detected after the single formal run. No output was changed or rerun; see append-only [POST_RUN_REVIEW.md](POST_RUN_REVIEW.md) and the separately registered successor [Issue #8622](https://github.com/Unjuno/agent-interface/issues/8622).

## Execution boundary and limits

Issue #7924's shared WSLc ownership gate remains HOLD, so no Docker/WSLc command was issued. This deterministic CPU fixture needed no container boundary and ran on the host. C: had 0 bytes free; earlier file-backed CLI test setup attempts failed with `OSError: [Errno 28] No space left on device` before formal candidate/auditor invocations; no files were deleted. The frozen in-memory process harness avoided output files and completed.

The fixture is hand-authored and does not validate production dependencies. No reliability rate, runtime availability, human benefit, latency, deployed safety, resource enforcement, or product-readiness conclusion follows. The original #8610 proposal and #8609 history are unchanged.
