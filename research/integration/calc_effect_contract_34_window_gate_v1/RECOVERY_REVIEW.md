# Recovery review: retained Calc VCL window-gate evidence

## Acceptance boundary

Disposition: **RETAIN_V1_V2_CONSTRUCTION_EVIDENCE_ONLY**. The original v1 **STOP_CONSTRUCTION** and later v2 **CONTRADICTED_WINDOW_VISIBILITY** remain separate historical outputs. Current v3 auditor qualification remains **HOLD_V3_AUDITOR_QUALIFICATION**.

This additive preservation review dated 2026-09-30 verifies published bytes and internal evidence bindings. It does not rerun an auditor, test, container, Calc/UNO, model or consumed allocation. It does not independently authenticate the historical processes, resource isolation, image execution, exit codes or test counts. No formal Issue #34, runtime, model, task-efficacy, latency, cross-app or product claim is promoted.

## Provenance and immutable originals

Source: [PR #4645](https://github.com/Unjuno/agent-interface/pull/4645), head [e557bc540a88018c95262ebac1f4e5d2dafd6d2d](https://github.com/Unjuno/agent-interface/commit/e557bc540a88018c95262ebac1f4e5d2dafd6d2d), tree `d1ef2ebec18c0516eb48a0500f8086ca1ea49ff9`. It follows [Issue #4643](https://github.com/Unjuno/agent-interface/issues/4643). Allocation: `calc-effect-contract-34-window-gate-20260927-01`.

All 11 original files below retain exactly their original paths and bytes under `research/integration/calc_effect_contract_34_window_gate_v1/`. Each retrieved byte sequence reproduced its Git blob ID and the SHA-256 shown here. The PLAN/runner/original-auditor blobs also match the identities stated in the original RESULT. These are current byte-identity checks, not independent proof of which bytes executed historically.

| Relative original path | Bytes | Git blob | SHA-256 |
| --- | ---: | --- | --- |
| `PLAN.md` | 2452 | `45b448ccb6fc1bd107769fcc0ffbe19418afa270` | `7950f5df746518e445b3622dbee479588e3de2bc62472adb5a9391045107c44d` |
| `RESULT.md` | 2759 | `dbfacbc38ac2416c0439188936fb96b24fa7d411` | `159b898fe8745e4fc11ce117a422b9ad6a8c929c6f6b01703e5a6d10f9f21d33` |
| `audit.py` | 3363 | `58b9c68783b1096c303931dd41790d46ff857502` | `31a1d1a5853cc2137dc5edb923b38588425fbc904083850c07c23736f4c59bd9` |
| `posthoc_v3/REVIEW_RESPONSE.md` | 2257 | `64f1d7c18a2726be35d74c347de3e2ddc5577f83` | `a3c53348d95c67d316a4d23c74175af020e1f23a462f8b24d8333cd613f4f278` |
| `posthoc_v3/audit_hardened.py` | 5297 | `6f5a2de934ce3ec2808229b6c6497df5100bd313` | `c2e61063a6fc81b8d8080ef0e5d3abe29eedef1079853d2396624ad1b7b86314` |
| `posthoc_v3/results/audit_v2.json` | 563 | `7107f77687733015917a70268ff3801ff67426e0` | `f6987b735cba78d71fef5efe0c7922c83d593640379d61d2f50a7a8829b77e9d` |
| `posthoc_v3/test_audit_hardened.py` | 3060 | `d1556e1c2ed0ba8eb5740b42123f7898c1b275a6` | `11be53c9d60a68117412988f5be53c1ef55570b580438a6c4820b36b680b6f16` |
| `results/calc-effect-contract-34-window-gate-20260927-01/audit.json` | 541 | `9356b5eb8bd2c088ae797d1ae208d5851cd85ad5` | `cdf8cf1a70af4a319230e7c66d85c0709ed9bf4d0126318da3b29f6be35432d9` |
| `results/calc-effect-contract-34-window-gate-20260927-01/baseline.xlsx.b64` | 6420 | `d8b2b15a7ac2456954b626e08c32bd9a06afee53` | `2a56d21c42743f662cc4ca46d948888fd0df9ae3de608beeeeb75c46dd3bb77e` |
| `results/calc-effect-contract-34-window-gate-20260927-01/raw.json` | 2876 | `d4e34222a30ad4a6e53a028aa96b80ab577b5f36` | `ee5fbd8fac9454d1c03110005761558beee325a6ef679fff74b1c2b62965ecca` |
| `runner.py` | 4802 | `32c50555d4c21fceef127c089612537c5a463876` | `a17a329b3bf354134075ea8921d741b5f495ca462f3de4228dcf9c9e7bb43cf9` |

## Exact historical v2 source recovery

The current `posthoc_v3/audit_hardened.py` and `test_audit_hardened.py` are revised v3 sources. They do not have the historical v2 source hashes cited by [the retained review response](posthoc_v3/REVIEW_RESPONSE.md). The exact earlier objects were recovered from commit [b3803870cca3e239715ddfe15815fc2a5612dec2](https://github.com/Unjuno/agent-interface/commit/b3803870cca3e239715ddfe15815fc2a5612dec2), before the v3 revisions:

- [Archived v2 auditor](historical_sources/posthoc_v2_b3803870/audit_hardened.py.txt): copied byte-for-byte from [original `posthoc_v3/audit_hardened.py`](https://github.com/Unjuno/agent-interface/blob/b3803870cca3e239715ddfe15815fc2a5612dec2/research/integration/calc_effect_contract_34_window_gate_v1/posthoc_v3/audit_hardened.py). 4,267 bytes; Git blob `7950f845781b72901bdcd2f4c0c26bafe5cb4718`; SHA-256 `4ed3ac03910e653a9855c34f966c0e732db68ca3c831cdc6dc7d46b0ff572f61`.
- [Archived v2 tests](historical_sources/posthoc_v2_b3803870/test_audit_hardened.py.txt): copied byte-for-byte from [original `posthoc_v3/test_audit_hardened.py`](https://github.com/Unjuno/agent-interface/blob/b3803870cca3e239715ddfe15815fc2a5612dec2/research/integration/calc_effect_contract_34_window_gate_v1/posthoc_v3/test_audit_hardened.py). 2,339 bytes; Git blob `3b9537d6563516a4fee70a055f270476450c882d`; SHA-256 `eee88b11040eeee75dabbb74da7333d7add20dfbd5d5987fd1e9d2c8b8853ede`.

Both hashes exactly match the v2 source declarations in the preserved review response. The `.py.txt` archival filenames avoid adding the old test to Python test discovery; their contents are unchanged, including original code and imports. They do not replace v3, repair either auditor, attest general correctness or authorize execution. Historical source binding is recovered; process authenticity is not established by these hashes.

## Independently checked retained evidence

Static verification used byte hashing, JSON parsing and standard ZIP/XML reading of the published workbook. No repository program was imported or executed.

- The retained raw JSON is 2,876 bytes with SHA-256 `ee5fbd8fac9454d1c03110005761558beee325a6ef679fff74b1c2b62965ecca`; both original and v2 output bind this same raw hash.
- The published base64 decodes to a 4,815-byte XLSX with SHA-256 `82dcdfb3febafdc1cd78bac6a925ae5f33d38adf5b79f970f433cfba739b69bc`. Its active worksheet A1 is 0 by independent XML inspection. This equals the raw before/after source-hash declarations and both audit source-hash fields.
- Nested root-tree and window-attributes command receipts both record exit 0. The unique `VCL ImplGetDefaultWindow` tree ID, raw stored ID, attributes command target and returned attributes header all bind to `0x20000b`. The retained attributes explicitly report `Map State: IsUnMapped`.
- A separate document-titled window `baseline.xlsx - LibreOffice Calc` at `0x200325` appears in the root tree, but this allocation did not retain its attributes. Its visibility cannot be substituted for the frozen VCL-helper target.
- Raw fields record initial A1=0, live A1=7.0, modified/unsaved=true, persisted A1=0, save/store count 0 and harness completion. These are internally consistent recorded fields; the live actions and historical environment were not re-observed by this review.

The retained row therefore contains positive contrary evidence for the frozen VCL-helper visibility requirement, rather than merely missing map-state evidence. This limited static observation does not certify the original experiment's process authenticity or the generic auditor.

## Preserve the three distinct stages

1. **Original v1:** [RESULT.md](RESULT.md) and [audit.json](results/calc-effect-contract-34-window-gate-20260927-01/audit.json) preserve `STOP_CONSTRUCTION`, with the sole stored error `same-run VCL window is not proven viewable`. The v1 audit stores map state UNKNOWN even though the raw attributes retain IsUnMapped. Its output and original interpretation remain unchanged.
2. **Historical v2:** [audit_v2.json](posthoc_v3/results/audit_v2.json) preserves `CONTRADICTED_WINDOW_VISIBILITY`, errors=[] and source-read mode `xlsx`. Its SHA-256 `f6987b735cba78d71fef5efe0c7922c83d593640379d61d2f50a7a8829b77e9d` matches the review response. The response reports six pinned-container tests and historical full-audit execution using a local workbook; those process claims and reported exit 1 were not independently replayed. The recovered source bytes establish the stated v2 source identities, not a newly generated v2 result.
3. **Current v3:** The current sources and tests remain unchanged and unqualified. No committed v3 full-audit output or pinned-container completion receipt is present in this 11-file bundle. The retained review response reports ten host tests and a blocked pinned-container re-audit. A [later comment](https://github.com/Unjuno/agent-interface/pull/4645#issuecomment-5852355284) reports host-side application of v3 to retained evidence; that prose is acknowledged as a separate historical claim and is not the v2 JSON or a committed v3 output. This recovery executes none of these sources.

The current-head review findings remain unresolved: [window-ID binding](https://github.com/Unjuno/agent-interface/pull/4645#discussion_r4113975760), [validation-error precedence](https://github.com/Unjuno/agent-interface/pull/4645#discussion_r4113975765), [effect-classification precedence](https://github.com/Unjuno/agent-interface/pull/4645#discussion_r4113975770) and [malformed nested JSON handling](https://github.com/Unjuno/agent-interface/pull/4645#discussion_r4113975772). Static source inspection agrees with these limitations. The explicit bindings above apply to this retained row only and do not resolve those generic auditor problems. Preserve the [publication-hold record](https://github.com/Unjuno/agent-interface/pull/4645#issuecomment-5852351042); retention is not v3 qualification.

## Downstream value and integration scope

[Issue #4667](https://github.com/Unjuno/agent-interface/issues/4667) and merged [PR #4760](https://github.com/Unjuno/agent-interface/pull/4760) created a distinct document-window allocation. Its [PLAN at inspected main](https://github.com/Unjuno/agent-interface/blob/cbca212667bc0c256184ef71bd8c1000d8c9a8aa/research/integration/calc_effect_contract_34_document_window_v1/PLAN.md) explicitly aims to clarify the #4643 contradiction; its [RESULT](https://github.com/Unjuno/agent-interface/blob/cbca212667bc0c256184ef71bd8c1000d8c9a8aa/research/integration/calc_effect_contract_34_document_window_v1/RESULT.md) preserves #4643's frozen row. Those two source blobs are `8926a8ac67da0d90564b11a479072032b7749172` and `deb67b05be7f59c5fcae93539c961f10a9878616`. Merged [PR #4901](https://github.com/Unjuno/agent-interface/pull/4901) adds an audit of that separate successor. None supplies v3 qualification for this original allocation or permits target substitution.

The original directory was absent at recovery intake main `cbca212667bc0c256184ef71bd8c1000d8c9a8aa` and package main `ad261f35965e0e292e533d2b88b780f22ce13585`. Retaining this missing negative predecessor supplies useful provenance for the already-merged clarification. The publication scope is exactly the 11 unchanged original files, two exact historical v2 source archives and this note. No original deletion, replacement, source fix, result reclassification, allocation retry, runtime change or numerical/generalization promotion is part of this preservation.
