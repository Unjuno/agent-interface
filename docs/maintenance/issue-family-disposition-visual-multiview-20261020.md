# Visual multi-view family crosswalk and disposition

Date: 2026-10-20
Repository baseline: `main` at `2920804cbea455bf9125b514e9d5bc03c0d1d1af`
Scope: Issues #7, #1946, #1968 and #2031; their directly related records only.
Method: read-only review of current Issue bodies/comments, merged/closed PR metadata, and committed canonical reports. No candidate, model, auditor, GUI, WSLc, or Docker execution was performed.

## Distinct questions

- **#7 — view-set utility:** Does choosing complementary views improve an independently scored task outcome enough to justify actual model-visible cost and latency under a fixed budget? This is the family-level open question.
- **#1946 — package integrity/size:** Can a typed multi-resolution package preserve the authoritative image while a reduced representation has fewer serialized bytes on a synthetic fixture? Its original PRs #1947/#1951 are closed without merge; the early size and duplicate-label claims are not accepted because review found pixel-buffer rather than canonical serialized-byte accounting and a non-ambiguous duplicate-label control.
- **#1968 — corrected package audit:** The corrected successor split the byte/reconstruction and duplicate-label checks into retained, distinct results. Issue #1968 is closed; its results do not establish model-facing utility.
- **#2031 — model-facing localization:** Does a deterministic truth-independent crop aid a multimodal model on a synthetic localization task? The T1 allocation was consumed; the saved result remains diagnostic and does not establish utility.

## Retained evidence crosswalk

| Record | Verified evidence | Disposition and limit |
|---|---|---|
| Original #1946 claims | Current Issue #1946 remains open. PRs #1947 and #1951 are closed without merge. The retained catalog records review defects in their original claims. | Do not accept the early `PASS` claim or describe it as a corrected serialized-size result. The old PR records remain history; no allocation is repeated. |
| Corrected serialized/duplicate-label result | Merged PR [#1981](https://github.com/Unjuno/agent-interface/pull/1981) retains `PASS_SERIALIZED_ATTENTION_DUPLICATE_LABEL_SCOPED`: three positional cases, exact reconstruction, reduced serialized bytes, one formal run and one audit. The report is [`serialized_attention_duplicate_label_successor_1968_v1/REPORT.md`](../../research/analysis/serialized_attention_duplicate_label_successor_1968_v1/REPORT.md). | Scoped synthetic result only. Crop selection is fixture-truth-derived; no model, automatic proposal, GUI, token, latency, or transfer claim. |
| Separate 24-row successor sanity | Merged PR [#1983](https://github.com/Unjuno/agent-interface/pull/1983) retains 24 local rows: FULL 6/6 exact, LOW_ONLY 4/6, CANDIDATE 5/6, CRITICAL 6/6; a largest-case CRITICAL package is 1,985 bytes versus 8,724 for FULL. The report is [`serialized_attention_successor_1968_v1/REPORT.md`](../../research/analysis/serialized_attention_successor_1968_v1/REPORT.md). | `HOLD_NO_FORMAL_CONTAINER`; this is local sanity, not a formal container result or model utility. Keep it separate from #1981's formal/audit pass. |
| #2031 construction | Merged PR [#2173](https://github.com/Unjuno/agent-interface/pull/2173) retains four provenance cases: one current-source coordinate mapping and three UNKNOWN controls for missing-target, stale-source, or overview-only inputs. The report is [`multires_provenance_construction_successor_2031_v1/README.md`](../../research/analysis/multires_provenance_construction_successor_2031_v1/README.md). | Construction only; it does not score model localization or byte reduction. |
| #2031 model T1 | Merged rescue PR [#6639](https://github.com/Unjuno/agent-interface/pull/6639) preserves 117 package blobs from the #6378 lineage. The canonical [README](../../research/analysis/model_localization_2031_gemma3gpu_t1_v1/README.md), [REPORT](../../research/analysis/model_localization_2031_gemma3gpu_t1_v1/REPORT.md), and [rescue qualification](../../research/analysis/model_localization_2031_gemma3gpu_t1_v1/RESCUE_PRESERVATION_QUALIFICATION.md) retain the result and limits. | Exactly 32/32 calls completed once on the named local Gemma 3 4B allocation. The per-arm `1/8` figures are invalid as pure accuracy because model selections omitted the scorer-required Boolean `abstain`. The auditor cap was exceeded after the initial read-only-mount STOP. The bundle has 113/114 manifest entries matching committed blobs; the REPORT entry is unresolved and original contemporaneous bytes were unavailable. The result is `NO_MODEL_UTILITY_DEMONSTRATED_ON_THIS_SYNTHETIC_ALLOCATION`, with protocol and report-custody qualifications; it is not a formal all-gates PASS. No rescore or model replay is authorized by this crosswalk. |

The #2031 model request/image byte and `prompt_eval_count` figures are descriptive retained observations only. In particular, overview-plus-crop had the largest recorded request/image bytes and prompt count, but the invalid accuracy scoring prevents a benefit inference. Keep its quantitative limits tied to the original report.

## Issue disposition

- **#1946: keep open / formal gate incomplete.** The original issue requires its complete multi-resolution fixture gate, an exact package/reconstruction check, and an independent audit. Merged #1981 is a valid but narrower three-case formal/audit result; merged #1983 is a broader 24-row local sanity result with `HOLD_NO_FORMAL_CONTAINER`, so it lacks the formal run and independent audit required to close #1946. The next exit condition is to run that exact frozen gate on a verified eligible new allocation, then preserve the full raw and audit result. Do not claim the original PRs were valid or that every original byte is mirrored into main.
- **#1968: closed.** Keep its distinct #1981 and #1983 result records separate.
- **#2031: keep open/actionable.** The saved T1 answers one diagnostic allocation; model utility remains unestablished and a valid corrected successor would need a fresh preregistration and separate authorization/allocation.
- **#7: keep open/actionable.** Its remaining experiment must compare fixed-budget view sets and independently scored task outcomes; package-byte savings alone cannot answer it.

## Next finite discriminators

For #1946, first establish an eligible new allocation and then run the exact frozen full-fixture package gate under the required container plus independent audit; do not replay a consumed formal allocation. For #7, prepare a separate preregistration only if the current task still prioritizes this family: use a same-model, held-out comparison with identical task semantics, response schema, and fixed model-visible budget; include overview-only, best single ROI, duplicate/same-information views, and complementary target-plus-destination views. Freeze an independent task oracle and report correctness, false target/abstention, correction count, actual image/token accounting, planner calls, end-to-end latency, and crop preparation cost. This receipt grants no new allocation, WSLc run, or model calls.
