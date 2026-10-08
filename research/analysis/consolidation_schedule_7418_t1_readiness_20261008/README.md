# Issue #8406 T1 readiness — 2026-10-08

## Disposition

`HOLD_T1_RESOURCE_AND_ALLOCATION_RECHECK`

No T1 model inference was run. The existing T0 A01 package remains immutable and scoped to its synthetic, deterministic schedule/audit contract. This note records readiness evidence only; it is not a T1 preregistration or model result.

## Checks performed

- The T0 A01 candidate and independent auditor were not rerun. Its frozen source and outputs remain in `consolidation_schedule_7418_t0_a01_20261008/`.
- T0 construction suite: 8/8 passed.
- Ollama reported no currently loaded model (`ollama ps`). The local daemon exposes installed model tags, including `gemma4:e4b`; tag presence does not establish that a model allocation is authorized or that enough memory is safely available.
- Host physical memory: 64 GiB. At inspection, `vm_stat` reported 4,165 free pages and 1,914,036 pages occupied by compressor; process RSS showed a large Chromium process (~12.3 GiB) and an Ollama service (~12.6 GiB). Memory pressure/swap activity is substantial, so loading a further model and issuing a 3-seed evaluation is deferred.
- GitHub GraphQL returned `API rate limit already exceeded` for issue/PR reads. The remote `main` was nevertheless fetched at `08d3283f6d3c61cc6b032c6c9c5a63ec464c07ff`, and merged into this work branch. PR #8414 could not be refreshed or verified through the API in this pass.

## Resume gates

Before a new T1 allocation:

1. Re-read the current #8406 body/comments and any active competing allocation; keep all raw evidence and packages separate.
2. Verify the #8414 PR state and whether a replacement PR is needed after the main update.
3. Recheck host memory pressure, active Ollama model use, exact local model digest/quantization, and whether local inference is within the issue's separately-authorized allocation.
4. If those gates pass, freeze the T1 model/version, prompt, decoding (including seed behavior), retrieval, corpus/order, held-out split, endpoint definitions, token budget, raw-output paths, and independent audit before the first generation. Keep three fresh seeds and all arm/checkpoint comparisons as prescribed by #8406.

No external API, GUI, user data, action, or deployed memory writeback is permitted by the T0 evidence. Do not treat T0 PASS as evidence of model behavior or transfer to production GUI memory.
