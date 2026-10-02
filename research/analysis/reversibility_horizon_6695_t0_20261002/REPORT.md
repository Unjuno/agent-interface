# Issue #6695 T0 — reversibility horizon boundary result

## Decision

**`PASS_SCOPED` for the authored deterministic state machine only.** Staging until the first informative signal changed the committed target from wrong to correct in the signal-1 stratum (1/1 vs 0/1). Waiting for the second informative signal changed the delayed-information stratum from wrong to correct (STAGE_1 1/1 vs STAGE_2 0/1). Neither staging policy improved the uninformative or no-correction-route controls. Deadline misses were 0/12. The independent auditor accepted all 12 unique traces with zero errors and every frozen gate true.

This confirms only that the specified state machine and auditor implement this result under stipulated signal/route semantics. It does **not** show that actual GUI feedback is informative, that a real action is reversible, or that staging improves a live agent task. It does not test #5428's broad option-accounting policy.

## Protocol and execution

Frozen allocation: `REVERSIBILITY-HORIZON-6695-T0-WSLC-20261002-01`; preregistration comment on Issue #6695 precedes formal execution. Intake main: `8c06589df01b2c4c1ab4017744faca61cab729f8`.

- Four fixed strata × three policies = 12 exhaustive first outcomes; no repeated pseudo-replicates.
- Candidate invocation: 1, exit 0. Independent auditor invocation: 1, exit 0. Retries/replacements: 0/0.
- Construction tests before freeze: 6/6 passed, exit 0.
- Candidate source SHA-256: `06267e52be3248facbd623e549a388b46f85bc32a75b328560b15503e4c01860`.
- Auditor source SHA-256: `4761ef52e4f88325e48333a6ece511c9419d9894232423154433a14ef21131d8`.
- Pre-registration design SHA-256: `91283975a52b73f54abaa85d7a8dfea9ffb3c28d9ff670538d4442c20284f05f`.
- Construction test SHA-256: `d473c6d6d09caed83012a7d9bf89317cc10012e5d14995ba8aa0e738f5459678`.
- Raw candidate: 5,294 bytes, SHA-256 `11cccbbe6b401e1ec2cabf6f8dceb96d9b855da8896756c3eb6ea766a91f0dea`.
- Audit JSON: 1,513 bytes, SHA-256 `74cbf4f986098e9d9bf169187d08e79a7cfceece7324fc174ab4d7d8383c9865`.

## Runtime

WSL 3.0.1.0, Arch Linux, native WSLc; Python 3.12.15, local image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`). Pull policy `never`, network `none`, CPU 1, 512 MiB requested. WSL warned that swap-limit capabilities/cgroup are unavailable; effective memory enforcement is not claimed. No GPU, model, GUI, user data, or external effects were involved; GPU acceleration is unnecessary for this 12-row CPU enumeration.

## Scope and next question

No statistical rate, latency, human benefit, real reversibility, live GUI, or production policy claim. The signal and correction-route transitions are hand-authored. A distinct future rung would need a permissioned fixture with independently scored draft/submit effects and actual correction/recovery verification; this result does not authorize it.
