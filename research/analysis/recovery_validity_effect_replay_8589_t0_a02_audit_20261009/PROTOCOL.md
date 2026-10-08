# Issue #8589 A01 left-gate audit-only protocol

## Question

Does the retained A01 `revision_left` row satisfy the frozen protocol's required strict advantage on the complete left-only schedule, when reconstructed independently from frozen `input.json` and `candidate_raw.json`? This allocation does not run a candidate, rerun A01's auditor, modify A01 files, or decide the broader method claim.

## Frozen gate

PASS only if: (1) copied A01 input hash matches the A01 freeze; (2) the unique `revision_left` input is complete-provenance and contains exact integer versions with only `left_cfg` changed from generation 1 to 2; (3) independent dependency/read-set reconstruction matches both raw recomputation lists; (4) selective recomputation is strictly smaller than earliest-conflict suffix recomputation; (5) no effect dispatch is present; and (6) the boolean-generation alias is rejected as a non-integer and is not used as the discriminator.

The independent auditor reads only copied A01 freeze, input, and candidate raw. It does not import or execute A01 candidate, auditor, or truth. Construction checks occur before freeze and do not write formal output. One formal invocation of the new auditor is permitted; retries are zero.

## Scope boundary

An audit-only pass establishes the narrow left-only decision-gate fact from retained evidence. It does not change A01's immutable records, validate all of A01, upgrade the A01 overall status, authorize GUI actions, or establish runtime/product effectiveness. No GUI, model, container, external effect, or candidate execution is involved.
