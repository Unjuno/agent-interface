# #1653 binary actor-witness root redundancy bound

Decision: **PASS_ACTOR_BINARY_ROOT_REDUNDANCY_BOUND_SCOPED**.

## Result

For five actor classes encoded across independent binary provenance roots, the minimum root count depends on the compromise model:

| threat model | criterion | minimum roots | retained codebook |
|---|---|---:|---|
| no fault | distinct codewords / d>=1 | **3** | `000, 001, 010, 011, 100` |
| one known bad root, erased | every deletion projection unique / d>=2 | **4** | `0000, 0011, 0101, 0110, 1001` |
| one unknown malicious root | disjoint radius-1 balls / d>=3 | **6** | `000000, 000111, 011001, 011110, 101010` |

The frozen negative controls find no five-actor code at m=2 for no-fault, m=3 for one erasure, or m=5 for one unknown Byzantine bit. Independent audit directly enumerates coordinate deletions and every zero/one-bit corrupted received word and independently searches each smaller root count.

## Interpretation

#1600 established that actor taxonomy cannot be finer than trusted witness information. #1277 established that a single current HMAC trust root cannot distinguish legitimate from compromised-key forgery. This successor quantifies redundancy when actor evidence is distributed over coarse independent binary roots.

A five-class actor taxonomy needs only three binary roots when all roots are honest, but needs four if one known root can be erased, and six if one unknown root can lie while exact actor recovery must continue. The distinction between known erasure and unknown Byzantine corruption is material and must not be collapsed.

These are coding/identifiability lower bounds, not proof that real roots are independent. Two keys held by the same process or hardware boundary may be one effective failure domain. Enough bits also do not imply freshness, scope binding, replay resistance, or privacy acceptability.

## Verification

- formal analytical invocation1; reruns/replacements/tuning0
- parent #1600 RESULT Git blob `91b4bf873337046101dc551ec8fb013db27858d0`
- parent #1277 RESULT Git blob `697d53777bd2b7bd621178ed577fb344271bc5fd`
- frozen audit PASS
- independent direct verifier PASS
- corruption controls 5/5 reject
- authority/task-success promotions0

## Next discriminator

A live successor should not add more synthetic roots. It should identify two or more **operationally independent** real provenance sources and measure whether their custody/failure domains are actually independent, including common-mode compromise, replay/freshness, scope binding, availability and overhead.
