# Optimistic concurrent read/write commit R0

Task `OPTIMISTIC-CONCURRENT-READWRITE-COMMIT-R0-20260919-001` / Issue #1723.

## H
With complete reconstructed read/write sets, non-reused semantic version identities, individually linearized check+effect, and no commutativity certificate, two intents may be generically admitted in parallel iff all prepared read versions remain current and there is no cross write/write or write/read hazard: `W_A∩W_B=∅`, `W_A∩R_B=∅`, `W_B∩R_A=∅`.

## T
Standard-library exhaustive finite model over four resources. Enumerate every `R_A,W_A,R_B,W_B` subset tuple and every external changed-resource mask: `16^5 = 1,048,576` rows. Compare candidate with independently structured oracle. Retain GLOBAL_SERIAL and WRITE_ONLY discriminators plus same-surface-disjoint and different-surface-shared-global directed controls. One formal invocation only.

## D
PASS iff candidate/oracle mismatch0; stale-read/cross-RW/WW unsafe parallel admissions0; global serial false serializations>0; write-only unsafe parallel admissions>0; directed controls and explicit hazard witnesses pass; formal1/reruns0; independent audit, source rehash and corruption controls pass.

## C
Completeness is assumed, not inferred here. #508 demonstrates bypass-read unsafety. Individual linearization is assumed. Independently proven commutativity can later relax W/W exclusion.

## U
Exact finite concurrency semantics only. No runtime speed, GUI correctness, conflict prevalence, token/model or production ABI claim.
