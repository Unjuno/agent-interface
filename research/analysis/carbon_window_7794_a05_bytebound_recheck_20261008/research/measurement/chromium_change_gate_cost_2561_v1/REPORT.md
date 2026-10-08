# Chromium change-gate cost: Issue #2561

**Decision: HOLD_NO_RUNTIME_SAVING.** Preserve this negative result; do not promote the hash-before-exact policy into the runtime. Evidence integrity passed. This is a controlled browser-rendered measurement, not application/task performance or natural collision prevalence.

## Lineage and scope

Intake main: `b2457b746a6df06f6536585dfe2ab937aff639f4`.
Lineage: closed #1564 -> closed #2001 -> existing open successor #2561.
Only `research/measurement/chromium_change_gate_cost_2561_v1/**` is added. No shared runtime, predecessor source/report, or parallel worker path is changed.

The full H/T/D/C/U and source hashes were posted before the formal directory existed in [freeze comment 5766190345](https://github.com/Unjuno/agent-interface/issues/2561#issuecomment-5766190345). The [first-result comment 5766366243](https://github.com/Unjuno/agent-interface/issues/2561#issuecomment-5766366243) retains the outcome. #2561 remains open: this measures ten authored canvas-template families, not ten independently sampled applications or independently human-annotated tasks.

## H/T/D/C/U

**H:** Exact fallback prevents false suppression of authored task-relevant changes, but charging both hash computations may cost more than exact comparison alone. Equal approximate hashes are not suppression authority.

**T:** One fixed allocation, `chromium-change-gate-2561-20260922-01`: 10 families x 5 variants x 6 strata = 300 pairs, each shared by three policies. Each stratum has 50 pairs. Text, selection, critical status, and large panel are task-relevant: 200 pairs, 20 per family. Labels and transitions are source-authored before capture. Candidates receive RGB bytes only. Chromium outputs actual 320x240 PNG rasters; both decoded RGB inputs and state receipts are retained.

**D:** Missing, malformed or contradictory evidence stops acceptance. Any task false suppression by fallback/exact fails safety. All 50 unchanged pairs must suppress. Scoped runtime value requires both pair-bootstrap and family-cluster 95% CIs for mean fallback-minus-exact cost to be strictly negative. The measured positive intervals trigger the preregistered HOLD. No tuning, allocation replacement or measurement retry occurred.

**C:** Python/NumPy dispatch, the 64-bit block-mean hash implementation, image size and native byte comparison affect this comparison. Precomputed/cached hashes, native implementations, higher resolutions and other workloads are untested. Balanced authored changes cannot estimate natural GUI prevalence.

**U:** No model calls, tokens, OS task input, X11 screenshot acquisition, task-success measurement, attention claim or product latency. Labels are candidate-blind under the authored fixture contract, not independent human annotation. Provided Linux execution container, Python 3.13.5, Chromium 144.0.7559.96, Playwright 1.57.0, Pillow 12.3.0, NumPy 2.3.5. Docker CLI and Docker image identity are absent. Browser requests are aborted and observed requests are zero; this is not OS-level network-none isolation.

## Analytical reduction

For deterministic h, equal pixels imply equal hashes. Thus a policy that checks exact bytes when hashes agree necessarily performs exact comparison on **every unchanged pair**, plus hashing. It cannot save exact comparisons in that stratum. This was recorded before the experiment.

The new hash uses 64 equal-area block means, thresholded with integer arithmetic: `64 * cell_channel_sum >= full_frame_channel_sum`. Both frame hashes are recomputed within each hash-policy call. EXACT_ONLY compares independent bytes objects; no same-object shortcut is used.

## First formal results

300/300 pairs; process exit 0; one invocation; retries 0. The excluded construction used six cases at variant 99; formal variants were 0..4. Independent raw-PNG/RGB reconstruction passed, including all seven corruption controls.

| Authored stratum | Pairs | Task-relevant | Global hash task misses | Fallback task misses | Exact task misses | Exact-fallback invocations |
|---|---:|---:|---:|---:|---:|---:|
| Unchanged | 50 | 0 | 0 | 0 | 0 | 50 |
| Benign one-pixel noise | 50 | 0 | 0 | 0 | 0 | 50 |
| Counter text | 50 | 50 | 50 | 0 | 0 | 50 |
| Selection marker | 50 | 50 | 45 | 0 | 0 | 45 |
| Critical status marker | 50 | 50 | 50 | 0 | 0 | 50 |
| Large panel | 50 | 50 | 0 | 0 | 0 | 0 |
| Total | 300 | 200 | **145** | **0** | **0** | **245** |

All policies suppress 50/50 unchanged pairs. Exact and fallback forward all 50 benign-noise pairs, whereas global hash suppresses them; this is separate from false forwarding on unchanged inputs. Pixel-change areas are 1 (noise), 38..52 (text), 54 (selection), 16 (critical), and 18014..18019 (large).

Timing uses 16-call batches after 16 excluded uniform-raster warmups per policy. Policy order is deterministically shuffled within pairs. Both hashes and applicable exact comparison are charged; capture, PNG decoding and transport are excluded equally. Values below are microseconds per call, amortized within each batch. The p95 is a percentile of batch means, **not** single-call tail latency.

| Policy | Mean us | Median us | p95 batch-mean us |
|---|---:|---:|---:|
| GLOBAL_AHASH_ONLY | 367.848 | 323.331 | 591.977 |
| AHASH_EXACT_FALLBACK | 377.981 | 336.540 | 640.736 |
| EXACT_ONLY | 6.940 | 6.426 | 11.244 |

Mean paired fallback-minus-exact gap: **+371.041 us**. Pair-bootstrap 95% CI: **[+357.030, +386.591] us**. Family-cluster 95% CI: **[+356.281, +386.392] us**. Each uses 1000 resamples with frozen seeds. These intervals describe the retained one-host corpus, not host-to-host or natural-workload variation.

Postmeasurement descriptive family breakdown (30 pairs and 20 task-relevant per family; no new decision gate):

| Family | Global task misses | Fallback calls | Global mean us | Fallback mean us | Exact mean us |
|---|---:|---:|---:|---:|---:|
| 0 | 15 | 25 | 364.857 | 368.616 | 5.647 |
| 1 | 15 | 25 | 393.427 | 342.793 | 6.290 |
| 2 | 15 | 25 | 333.734 | 355.520 | 7.334 |
| 3 | 10 | 20 | 372.743 | 373.029 | 5.632 |
| 4 | 15 | 25 | 343.194 | 422.433 | 6.053 |
| 5 | 15 | 25 | 347.806 | 379.886 | 6.385 |
| 6 | 15 | 25 | 362.665 | 383.854 | 6.371 |
| 7 | 15 | 25 | 345.399 | 348.171 | 5.871 |
| 8 | 15 | 25 | 388.459 | 416.601 | 5.861 |
| 9 | 15 | 25 | 426.201 | 388.904 | 13.955 |

The excluded uniform-raster tracemalloc probe reports peaks of 9372/9436/28 bytes for global/fallback/exact respectively. These are Python-visible allocation diagnostics, not native/browser/RSS totals or a formal memory benchmark.

## Predecessor correction without rewriting history

Byte-bound reconstruction of #2001 source matched Git blob `1a2f4addb5abfb288d3869878b9188338f94dc75`. Original stdout was `cases 6 task_false_suppression 1 fallback_catches 1`. Its collision is the **panel brightness** case, not `task_micro`. Its hash thresholds each of 512 pixels rather than 64 block means. Unequal-hash cases forward through the hash leg; the original fallback counter is not a total forward counter. The source and six-case reconstruction are retained as `predecessor.py` and `PREDECESSOR_AUDIT.json` inside the bundle. Old files/results remain unchanged.

## Revalidate from this GitHub directory

Prerequisite for pixel restoration and audit: Python with Pillow (measured version 12.3.0). No browser or NumPy is needed for revalidation. From the repository root, use a new output path:

```sh
python research/measurement/chromium_change_gate_cost_2561_v1/restore_compact.py \
  --out /tmp/issue-2561-revalidation-01
```

The command verifies eight chunk hashes, compressed/payload hashes, restored text-file hashes and all **300 original RGB frame hashes**, then runs the unchanged frozen `audit.py` in a separate process with seven corruption controls. It compares every scientific audit field to the original `AUDIT.json`. It does **not** launch an experiment or create new timing measurements.

GitHub stores the exact measured RGB pixels, original raw row/timing/receipt bytes, frozen sources/plan, process/environment records, original audit and predecessor audit in a lossless compact bundle. Original browser PNG **encodings are not in that bundle**. The restorer creates explicitly derived PNG encodings and an alternate row view; original rows and original PNG digests stay unchanged. Only total PNG encoding byte count differs in the audit view (original 1,332,597; derived 1,488,884 under measured Pillow). The complete conversation archive also retains all original PNG files.

Original rows SHA256: `e422f6c30152b3185f58c324c21ece736309cd3328317499e7cff79a4635a2e3`.
Compact payload SHA256: `217571f71e18300dfecc231ce968588970e9807db5c360894d9781542e2d3c24`.
Local revalidation result: `PASS_COMPACT_PIXEL_REVALIDATION`, all 300 identities matched; all scientific fields equal. Construction metadata is retained but construction PNGs are in the full archive only.

A postmeasurement attempt to recompress a single PNG IDAT chunk failed with an incomplete zlib-stream error. It neither modified formal/source bytes nor triggered a rerun. `PACKAGING_NOTES.md` retains this delivery failure separately from the successful measurement.

## Bounded roadmap and handoff

Source reconstruction, excluded construction, public preregistration, the single 300-pair measurement, independent auditing/corruption controls and lossless pixel revalidation are complete. PR publication integrates evidence only; it is not runtime promotion or repository-wide ROADMAP completion.

Stop reason for this allocation: the preregistered runtime-value gate failed, while evidence integrity and scoped fallback safety passed. Do not reallocate or tune this corpus to obtain a PASS. Keep EXACT_ONLY as the measured baseline. Remaining scientific work belongs to a separately frozen successor: independently sampled application families and semantic labels, then an explicitly charged native/cached-hash comparison at relevant resolutions. Natural collision prevalence and task benefit remain unanswered. The broad #2561 is not closed by this evidence PR.
