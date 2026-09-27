# Route capability contract v1 — retained first outcome

Task `ROUTE-CAPABILITY-CONTRACT-20260917-001`, Issue #828. BASE `40072ec1962afe9fe1a9f6ade79ce36a2e8cc93f`.

## Result

Retained disposition: **`FAIL_PREREG_BASELINE_DISCRIMINATOR_RETAIN_CANDIDATE_GATES`**.

The frozen formal runner was invoked exactly once over 10 requests. The dimension-aware candidate selected only routes whose retained verified dimensions covered the requested contract in all 10/10 rows, returned `UNSUPPORTED` when the centered contract had no sufficient route, never selected the one-contact negative, and rejected unknown dimensions/provenance. The flat baseline selected `native_fixed80` for centered semantics where center had failed in #803.

The frozen auditor returned `PASS_EFFECT_DIMENSION_CAPABILITY_NEGOTIATION_SCOPED`, but independent postformal verification found a preregistered discriminator/auditor defect: the prereg required exactly two baseline false admissions, while the frozen matrix actually contains three (`center-fallback-wheel`, `center-native-only`, `center-insufficient-only`). The frozen auditor counted only two named rows. Therefore its PASS is retained but not adopted as the experiment disposition.

A first postformal corruption-control harness also contained a targeting error: its attempted candidate-route corruption changed a valid row and was not rejected. That output is retained. A corrected diagnostic changes only mutation targeting and is rejected 5/5. Neither diagnostic changes the formal result.

## Integrity

- formal invocations: 1; reruns: 0;
- retained #792 scale audit Git blob: `389fe8cd93603c0415480fc398664a903dede0f4`;
- retained #803 center summary Git blob: `28bc4a8c07958db58efe98eb73881cbced46c481`;
- formal result SHA-256: `3fc69fe7b0c73dad773719005dbf860c6a78696296bb91aacc76ed94e3a4e525`;
- frozen audit SHA-256: `684f488713efbd65cacac8396edf81d5d5e3dff50f93ca17f53008518e145dc6`;
- independent verifier SHA-256: `c4b8f65ef753d9d21a2392339f748cb1f3f244eb845278c3daeb69c00572c1ec`;
- corrected corruption controls SHA-256: `4a9f6fd8860fcacfb836f4ea76411404c663a27cb7ad735f3738cd10725ac423`;
- frozen source rehash after formal: exact, zero mismatches.

## Interpretation

The mechanism evidence is encouraging but the preregistered experiment fails its own measurement contract. Do not relabel v1 as PASS. The only justified successor is a new identity that keeps candidate policy/evidence/request semantics fixed and repairs only the baseline-discriminator enumeration/auditor coverage before one fresh deterministic allocation. No GUI/model/device input or runtime mutation occurred.
