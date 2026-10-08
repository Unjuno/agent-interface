# Native Inkscape: scoped SVG edits and the raw-attribute / visible-effect boundary

Decision: RETAIN scoped current-document editing and limited refusal of unsupported paint contexts. HOLD production promotion. Issue #344. Publication BASE `0dd239b7db10831a4e8ac078d3a32d4be6370e3d`; additive `research/cross_domain/svg_scoped_edit_v1/**` only. PR #334 remains separate; no shared runtime, historical result, workflow or other allocation was changed.

## Actual application boundary

Installed native Inkscape1.4 selects explicit ID `target`, applies `object-set-attribute:fill,#008000`, and exports plain SVG. It also renders final documents to PNG. This is NOT GUI/XTEST/Executor/InputOwner or a model/Doom run. Local bare Git is the explicitly added publication owner: build a candidate parented to the inspected current commit, then update the ref with that exact expected old OID. Inkscape alone is not claimed to supply CAS or concurrent open-GUI synchronization. All data are generated disposable fixtures.

## A: partial-document preservation

Authored task: recolor only the target rectangle from red to green; preserve all other current SVG attributes/elements, both rectangles' positions, separate repository note and current ancestry. Refuse a concurrent target-fill change or a ref change after validation. Position changes are explicitly compatible with this task, not generally irrelevant.

All three policies share unique target-ID validation, old target-fill precondition and final expected-OID publication. `stale_document` edits the original document. `whole_file_guard` edits the current document but refuses any document-byte change. `scoped_current` edits the current document while checking only the declared target paint attribute. Source-document choice and guard granularity are two ablations; the three-arm comparison is not one universal single-factor contrast.

Original A freeze `41b53d2b2af27e5dd5c6186c160637c88e3bbece` remains INCOMPLETE:22 complete,1 partial (`A-r2-whole_file_guard-target_move`),22 unstarted. The all-case command hit the180-second container ceiling. An earlier unsupported interactive launch started no shell/case. The prefix and partial evidence remain retained, never pooled with A2; no consumed ID was rerun.

A2 freeze `3c36db3e1bdc6d9f48fb9cfd69460e7a00d5afb0` changes only supervision to synchronous five-case blocks and fresh allocation/IDs. Experiment/auditor bytes, policies, geometry, order and gates are unchanged. All45 first outcomes completed:five schedules x three policies x three matched geometry repetitions.

| Schedule | Stale document | Whole-file guard | Scoped current |
|---|---:|---:|---:|
| Stable |3/3 correct|3/3|3/3|
| Other rectangle moved |0/3; reverted|0/3; false refusal|3/3; preserved|
| Target rectangle moved |0/3; reverted|0/3; false refusal|3/3; preserved|
| Target fill changed |3/3 refusal|3/3 refusal|3/3 refusal|
| Ref changed after validation |3/3 refusal|3/3 refusal|3/3 refusal|
| Total |9/15|9/15|15/15|

Scoped current has nine successful edits and six correct refusals, NOT15 edits. Stale-document delivery causes six out-of-scope geometric changes; whole-file guarding causes six false refusals. This transfers the write-footprint lesson to a real document editor, with a conflict unit smaller than one file. It does not establish automatic operation-footprint discovery.

## B: green attribute, blue pixels

Separate construction added CSS after the original red-paint intent: either target inline `style="fill:#0000ff"` or document stylesheet `#target { fill: #0000ff; }`. Native Inkscape changes the presentation attribute to green, but the rendered target remains blue. This is expected CSS/presentation-attribute behavior, not an Inkscape defect or fabricated exit code.

B freeze `e6d6587ab95b8eacad0afd01931de9265a7e87ba`:three conditions x two policies x three repetitions =18 first outcomes. Native editing commands are identical when admitted. `raw_attribute` checks only raw fill; `paint_context` additionally refuses this primitive's unsupported stylesheet/inline-style context. It neither computes arbitrary CSS nor repairs styled recoloring.

| Condition | Raw-attribute guard | Paint-context gate |
|---|---|---|
| Stable plain SVG |Green effect3/3|Green effect3/3|
| Concurrent inline CSS |Inappropriate publication3/3; green attribute, blue pixels|Refusal3/3; unchanged document|
| Concurrent stylesheet |Inappropriate publication3/3; green attribute, blue pixels|Refusal3/3; unchanged document|

Raw-attribute policy is correct3/9. Paint-context is correct9/9:three edits and six refusals. In the CSS controls the image equals the expected unchanged conflict image, but the unrequested raw-attribute mutation/publication still violates the contract. Thus screenshots alone also miss part of the failure. Structure AND visible effect are checked. A2 and B are separate scoped comparisons, not a combined production test.

## Independent verification and failure accounting

The frozen auditor imports no experiment code. Candidate uses lxml; independent structure verification uses ElementTree. It reads native Git objects, full expanded SVG element/attribute structure, both repository entries, parent commits and reflogs. A separately implemented integer-rectangle rasterizer, which never invokes Inkscape, predicts every RGBA pixel; Pillow decodes actual PNGs. Integral opaque geometry limits this oracle to the authored fixtures. Task-expected structure and render are checked separately from actual-document rendering integrity.

Complete comparisons:63/63 evidence-integrity passes, but task-contract correctness across controls45/63. Native calls:42 edit/export plus63 final PNG exports =105, excluding incomplete A/construction/tests. Full image comparison covers4,032,000 pixels across63 images; pixels are not independent trials.

Twelve test methods passed before scoring and again after independent archive extraction. Corruption controls reject wrong reasons/eligibility/hash, Boolean or reversed clocks, and a changed pixel; missing/duplicate targets, native late-ref race and consumed-directory refusal are tested. Re-extraction verifies3497 manifest files with zero mismatches, byte-identical A2/B audits, all frozen source hashes and the22-case incomplete-A prefix. No measured-ID reruns. A2/B have no unexpected harness failure; original A remains incomplete.

Construction action-list output initially hit locale conversion failure; a separately recorded C.UTF-8 invocation succeeded and that locale is pinned. Headless warnings remain in raw receipts. Output correctness is never inferred merely from return code0.

## Conditions and limits

Intel Xeon Platinum8370C, CPUs0-4, shared host/unpinned frequency,batch1; CPython3.13.5/Linux6.18.44/glibc2.41; Git2.47.3/SHA1 bare repositories; Inkscape1.4(e7c3feb100,2024-10-09); Pillow12.3.0,lxml6.1.1. Generated320x200 simple SVGs. The CPU model's2.80GHz text is not a measured/fixed clock.

SVG units equal raster pixels only in this fixed viewport; no physical length is inferred. Same-host perf_counter_ns integer timestamps are checked for order, not used to claim speedup. No calibrated combined uncertainty or coverage factor. Three authored geometry repetitions are not natural failure-rate samples. No generic SVG/CSS, live GUI synchronization, automatic dependency discovery, same-ID incarnation, remote writer, power-loss, production or actual-agent-performance claim.

H: current document plus scoped write precondition preserves compatible edits; raw attributes need not prove visible paint. T: incomplete A retained; frozen A2(45) and B(18), native editor, independent structure/raster verification. D: retain A2 scoped15/15 and B limited refusal9/9; HOLD general promotion. C: authored semantics and additional Git publication boundary explain the result; the CSS candidate refuses rather than solves unsupported cases. U: one host/version, small prescribed fixtures, no arbitrary footprint discovery or speed measurement.

Related fields: document editing at property granularity; database read/write conflict validation; graphics/CSS semantics versus serialization. These are design connections, not three application benchmarks.

Next question: can an effect-owner computed-paint/operation contract permit style-based recoloring while preserving unrelated style properties, rather than guessing from an attribute or refusing all styled objects?

## Retention and primary references

Exact executable source/plan archive, freezes, all63 per-case verdicts, summary and validation are retained here. Full native repositories/logs/SVG/PNG outputs, original incomplete A and construction artifacts are conversation-only:193956-byte raw archive, SHA256 `6ffb266205be2204d40326cf7e0dcdc6abea7d2af9289fc17bae2d7c3b83b77c`. Source archive9956bytes,SHA256 `674f4da497cb047df5b849507e3678005d2761e7047f12d970e1a0d0f5236adc`, Git blob `2304f905b9cb3daf0b4f7835491a1d31a2dad786`. No fonts or installed binaries distributed. Longer report is in the raw archive.

Official references: https://wiki.inkscape.org/wiki/Using_the_Command_Line ; https://git-scm.com/docs/git-update-ref ; https://www.w3.org/TR/SVG2/styling.html . Pinned installed action-list and measured behavior determine the claims, not newer documentation alone.
