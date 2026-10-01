# Chromium procedure -> guarded typed macro v1

TASK: CHROMIUM-PROCEDURE-GUARDED-MACRO-20260917-001
BASE: e4b7f2589d807bfc9e3c688bc3906131a70b779c
Issue: #890. Parents: #857, #57. Related: #876.

H: a deterministic compiler can discard task1 absolute GUI coordinates and retain only the frontier-authored semantic procedure as a typed guarded macro over token/field_handle/submit_handle. Reuse should admit A, yield on task4 old-handle missing, and admit B after fresh repair without recompilation. A literal coordinate replay remains apparently admissible under unchanged window context but mismatches retained B targets.

T: container-only retained-evidence replay over exact source blob fde6950c45e216956a774e71830c5af7298d0000. Compile from task1 only. Six states x two artifacts = 12 formal rows. One invocation, reruns 0.

D: PASS_CHROMIUM_GUARDED_MACRO_COMPILATION_SCOPED iff candidate has no absolute target coordinates/fixed token, A positives admit, task4-pre yields before pointer, B post/5/6 admit current B handles without recompilation, literal replay exposes historical-coordinate mismatch on B, controls/audit/integrity pass.

C: this may only restate semantics already hand-implemented by the persistent client; source output may be insufficient without compiler-side vocabulary; retained evidence does not prove new live task success.

U: one Chromium field-entry procedure, one retained A->B layout transition, read-only replay only. No model/GUI execution or general compiler claim.
