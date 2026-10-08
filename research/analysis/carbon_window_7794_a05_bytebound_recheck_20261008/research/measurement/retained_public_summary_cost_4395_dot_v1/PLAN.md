# Real retained public-projection cost, v1

Status: construction complete; not yet executed. One parent-authorized invocation requires independent pre-run approval.

## H: the exact question

On a fixed corpus from actual retained Tk use, characterize the incremental projection plus external metadata-serialization cost of the existing FULL_V3, PACED_BRIEF and PUBLIC_SUMMARY choices. Exact required diagnostic preservation is the primary gate. Timing and traced allocation sizes are descriptive outcomes, not a presupposed speedup.

Closed #4395 measured synthetic no-image receipt compaction before the later public-summary path. public-summary-01 already measured same-report byte counts but no projection CPU/allocation. This fills one real-input local-stage boundary and creates no new runtime optimization. #3544/#57/#2789 remain open.

## Sources and inputs

SOURCE_ACQUISITION.json identifies the exact rechecked main and four Git blobs. Three whole unchanged modules execute: public_summary.py, public_presentation.py and their pure sequence.py dependency. mcp_server.py.readonly is a pinned read-only provenance source only; it is never imported.

The corpus derives from the 260194-byte public-summary-01 archive, Git blob 2c181c56825f9cc0d3c646ce8cc07e68ee6c207b, SHA256 b44b25eadd1fc17d0ebcd4b5ce13ae18750c3cd1e127c5bb6f377ac1be3514d3. The full archive, manifest and selected member hashes were checked before construction.

- entry-full: exact full-2.json, SHA256 b99750db61054eee3dcfcef7a82b642eb41ebe3e21fd703b3a6af8f3ea4a121e
- save-full: exact full-3.json, SHA256 6fe75f3baf681cd6768e94fb4feebaa418e189eb2594b882adefe4d77eebbaf1
- refusal-full: the single actual text block from reply-5.json, whose original SHA256 is 436eb658d99dd6c19a077f858ce6ca5187a118884379aa3b6a953166875634bd; decoded text SHA256 e798af97e13d88f9282f46e0c36140a480cf1aa3a6ca743e0076d4ed466de921

Two expected summaries are the single actual text blocks from original replies 2/3. Their decoded text hashes are 0f88ec168394641db176ed73e9e77e34a6ae8a6a98a9cd008f17245f7882803a and 9938afcea46feb072abdec3ba25dec5b3d295286d6d68fdc5130d038a9a246a9. No report path or field is rewritten. These are existing metadata objects with image references; image payload and SDK/envelope transport are excluded.

## T: frozen measurement and allocation boundaries

Three unchanged policies:
- FULL_V3 directly serializes the existing optimized full-reference view. No artificial deepcopy is added.
- PACED_BRIEF invokes existing brief_public_report. Nonpaced save and actual refusal retain the existing full fallback.
- PUBLIC_SUMMARY invokes existing summarize_public_dispatch.

External metadata encoding exactly follows mcp_server.content's dict(value), pop(image), json.dumps(metadata, allow_nan=False), with default separators, insertion order and ensure_ascii. UTF-8 encoding is included. Projection-internal canonical JSON remains unchanged. MCP SDK object/envelope creation and image blocks are excluded.

Fixed case order: entry, save, refusal. Within every case use all six permutations of the three policies in itertools.permutations order:
1. FULL, BRIEF, SUMMARY
2. FULL, SUMMARY, BRIEF
3. BRIEF, FULL, SUMMARY
4. BRIEF, SUMMARY, FULL
5. SUMMARY, FULL, BRIEF
6. SUMMARY, BRIEF, FULL

First run every warmup block: one call per policy/order/case =54 calls. Then every measured block: three calls per policy/order/case =162 calls in54 aggregate timing records. Each case/policy has six three-call aggregates. Positions and pairwise precedence are balanced. Technical repeats are not new tasks or population samples.

The named timed block includes three whole projection+serialization operations, Python call/loop/list-append overhead, and retention of all three output byte strings until after the end clock samples. Per-call division is a batch estimate, not an isolated-call latency. Output hashing, journal writes/fsync, imports, corpus parsing, independent audits and source checks are outside measured brackets.

Before any projection call, collect64 empty wall/CPU bracket pairs. A measured wall AND CPU aggregate must be at least max(1000*reported wall resolution, 1000*reported CPU resolution, 100*median_low(empty wall bracket), 100*median_low(empty CPU bracket)). Keep all empty samples, including outliers. This is a conservative measurement-resolution gate, not calibrated uncertainty. Failure means STOP_CLOCK_GRANULARITY; do not increase repetitions or retry.

After timed blocks, make nine separate untimed tracemalloc observations, one per case/policy. GC runs before tracing; imports and source objects already exist. Start tracing with one frame, reset peak, execute one projection and serialization, retain both returned projected object and serialized bytes until reading current/peak, then stop tracing. Report net=current-minus-baseline and peak-minus-baseline tracked Python bytes. No snapshot statistics, RSS ceiling, leak rate, retained-cache bound or population claim follows. FULL aliases the preexisting source; this honest lifetime difference is part of the policy comparison.

Total unchanged policy calls225 =54 warmup +162 measured +9 memory. Zero GUI/action dispatch. No sleeps, artificial delays, duplicated input content, adaptive sample size, network experiment, model, GPU, install or user-machine access.

One Python process, one pinned available logical CPU, RLIMIT_AS256 MiB, RLIMIT_CPU15s, outer timeout30s. Entire invocation, including audit/controls, stays inside that outer window. An exclusive new output directory and exclusive outer stdout/stderr/exit receipts prevent overwrite. No rerun/tuning after first outcome.

## D: independent audit, controls and dispositions

oracle.py imports no candidate or harness. It reconstructs the finite paced-brief representation from the raw source, compares success summaries with the actual independently retained delivered summary texts, and demands exact typed canonical equality for FULL/save-BRIEF/refusal fallbacks. The actual serialized output bytes and SHA256 are retained separately.

It checks complete source/inputs/freeze identity; before/after input object hashes; exact fixed row schedule; every repeated output hash; external serializer spacing/order; unchanged outcome/session/call/image/source fields and all capture/release/activation records; timing type/granularity; memory type/order; complete call accounting. Summary omissions remain explicit and are never called lossless.

Twelve effective copied-evidence controls:
1. omitted release
2. changed outcome
3. changed source digest
4. wrong call identity
5. wrong full-retrieval call
6. refusal mislabelled completed
7. changed wait count
8. integer1 replacing true release flag
9. missing measured row
10. Boolean wall duration
11. nonfinite memory count
12. changed source hash

For the eight output controls, update output digest/byte count and every repeated hash coherently, so rejection must come from semantic/preservation checks, not just stale copied hashes. Canonical JSON verifies the mutation is effective, distinguishing Boolean true from integer1. Keep each changed artifact and rejection. These controls are synthetic evidence-validation perturbations, not empirical failure incidence.

PASS_RETAINED_PUBLIC_PROJECTION_COST_CHARACTERIZATION requires all gates, all225 calls, all12 controls rejected, exact source-before/after identity and exit0. Timing/byte/allocation superiority is not required. Semantic/evidence mismatch is FAIL_PRESERVATION_OR_EVIDENCE; coarse clocks STOP; failed controls HOLD; exceptions, source/resource/output failures STOP_EXECUTION_OR_PREFLIGHT. Preserve first raw journal, output, error and actual outer exit even on failure.

## Construction chronology

Two helper red/green cycles are retained (9 then2 expected assertion failures). Initial complete local construction had13 passing tests; after pre-run review corrections, the complete package has15 passing tests. The raw-audit construction fixture combines retained metadata with explicitly fabricated clocks/memory to test the verifier and12 coherent corruption controls; none of those invented measurements is formal evidence. Candidate projection modules have not been imported or run during construction. A static source transfer newline correction is documented in SOURCE_ACQUISITION.json. A static variable-shadowing receipt issue was corrected before candidate execution.

The measurement runner is not a project-wide repository test run. Native/GUI/model suites are outside this isolated package and unavailable in this budget; no broader suite claim follows.

## C/U and integration limits

Two successful operations and one planned refusal from one Tk session. Warm-process measurements, host frequency/load and allocator state are uncontrolled; six aggregate samples per cell support descriptive summaries only. The original byte savings are already known; new information is the current incremental CPU/allocation cost and preservation on these exact views. Full-report retrieval cost, image delivery, model interpretation/tokens/fees, useful feedback, semantic completion, GUI speed, task correctness, cross-app generalization and default adoption remain unmeasured. No current source authority or permission to replay an action follows.

Publication is additive only after parent review, under a fresh unique research namespace. Original #4395, source corpus, scientific results, T2 evidence and all consumed allocations remain unchanged.


## Pre-run review correction, formal invocation still zero

The first proposed freeze SHA256 828a4fc5bb0c2cb8b89bbf479b158905015b8cab5b50929cdb7f5aa64a31c0aa was rejected before execution for two receipt/granularity issues. It and the exact old runner/oracle are retained under pre-review/. A further two-test red/green cycle proves the fixes. Empty-clock medians may be zero; reported resolution and the actual aggregate gate still determine adequacy, and genuine clock failures are STOP. Actual getrlimit/affinity preflight is now persisted before imports; a final source/output/resource receipt is written in finally for every normal PASS/FAIL/HOLD/STOP and catchable exception. Forced termination still requires the outer timeout/exit receipts. No candidate call occurred during these changes.
