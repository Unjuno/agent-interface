# #1286 first outcome — frozen audit integrity failure

Task `MAP01-HEADING-PULSE-PRECONDITION-20260918-001`.

## First outcome
**FAIL_INTEGRITY_FROZEN_AUDIT_DISPLAY_TYPE**.

Twelve fresh first sessions completed, same-ID reruns0. Scientific rows are coherent: 45 ms candidate converged6/6; 190 ms baseline converged4/6 with two 8-pulse two-angle cycles; release failures0; deaths0. Candidate max pulses7 and max final absolute error3.515613° under the frozen strict <4° envelope.

However the source-first frozen auditor compared runner `display=":350"` to schedule `display=350` without normalization. It therefore emitted12 display-only integrity errors and returned FAIL. The allocation is not promoted to scientific PASS and is not rerun.

A separately labelled postformal read-only diagnostic changed only that display comparison and passed all scientific gates with errors[]. This diagnoses the audit-representation defect but cannot retroactively repair the frozen allocation.

## Stop / successor
Do not rerun #1286. A fresh harness-only successor may change only audit display normalization while holding heading runner, offsets, pulse durations, strict<4° tolerance, settle, pulse budget, runtime and decision gates fixed. Fresh formal sessions are required for a clean first outcome.

Raw FORMAL_RESULT SHA-256 `0a14134584579fffd253cb2c218cce11ed971ed726a5762035fc77b9f0162dc7`, retained losslessly as deterministic gzip+base64 parts.
Posthoc normalized audit SHA-256 `2503e1ad325bef73ddad8d7bd62c2d2244e049474c3b99660014b49820aaf6b8`.
