# Instrumentation-bypass read-set failure — Git delayed delivery rung 6

Decision: **RETAIN_INSTRUMENTATION_BOUNDARY_COUNTEREXAMPLE**.

## Question
Rung5 showed that a runtime-observed read-set receipt can recover a dependency omitted by planner self-report when all semantic reads traverse the tracing adapter. This rung changes one thing only: `hidden.txt` is read directly with `git show` in the bypass arm, while it remains a real dependency of the authoritative predicate.

## Frozen experiment
Premeasurement freeze `8d68ffb1d9ccb2421c7098a3dcf4a1893844df61`, publication base `ba407ec2cabe0650962f8b7a87e671491336479e`. Thirty fresh Git2.47.3 repositories: all-traced vs hidden-bypass x stable/hidden-change/unrelated-change x5. No measured ID rerun.

| Policy / schedule | Correct | Rejects |
|---|---:|---:|
| all_traced / stable |5/5|0|
| all_traced / hidden_changed |5/5|5|
| all_traced / unrelated_changed |5/5|0|
| hidden_bypass / stable |5/5|0|
| hidden_bypass / hidden_changed |**0/5**|0|
| hidden_bypass / unrelated_changed |5/5|0|

In the bypass arm the semantic predicate still reads `hidden.txt`, but that direct read is absent from `plan_read_set`. Revalidation therefore sees only `declared.txt`, concludes the delayed effect is valid, and writes B after the hidden dependency changed.

## Interpretation
Observed-read provenance is stronger than planner declaration but is **not inherently complete**. The soundness condition moves from “planner listed every dependency” to “every semantically relevant read crossed the capture boundary.” Identity-bound Git CAS cannot repair a missing semantic dependency; it only binds the write to the state that was actually checked.

This deliberately does not test a fix. Whole-process system-call tracing, language/runtime sandboxing, effect-owner dependency APIs, and application-authored validity receipts are separate candidate mechanisms.

## Verification
Frozen auditor passes all30 retained rows according to their expected positive/negative roles. Independent extraction reruns 5/5 tests, reproduces the audit exactly, and verifies1,417 files /1,002,373 bytes with zero hash mismatch. Raw archive is conversation-only:47,916 bytes,SHA-256 `856d640ccc0a863ec71293c7046f9891a2752858b9dbc1d729dd3852dc9cc804`.

## H/T/D/C/U
**H:** bypassing the read instrumentation will omit a real dependency and make the receipt unsound.  
**T:** fixed30-case Git matrix, same semantic predicate and final CAS, only hidden read route changes.  
**D:** PASS as a counterexample: hidden-bypass stale-writes5/5 while all-traced rejects5/5.  
**C:** a stronger interception boundary or effect-owner validity API may restore completeness.  
**U:** one local Git fixture; no evidence for OS-level completeness, arbitrary GUI dependencies, model inference, network or power-loss behavior.
