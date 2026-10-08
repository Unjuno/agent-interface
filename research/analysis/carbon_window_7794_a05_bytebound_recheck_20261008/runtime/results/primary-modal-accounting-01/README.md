# Primary Calc modal accounting and integrated image-reuse admission

Disposition: HOLD for efficiency/human-tempo adoption; the recorded-reply integration gate passes. This is additive analysis of `primary-target-tools-live-04`, not another live task, a matched comparison, or completion of #57/#56/#2789. The frozen live report and all three earlier construction failures remain unchanged.

Source: main `14b81dd1f6853623a694266b98538f812847257a`. Host/primary exchange are the existing production modules. Environment rechecked 2026-10-02 JST: WSL package 3.0.1, Ubuntu 24.04.4 using WSL2, kernel 6.18.40.1, physical Node 24.13.1 and Python 3.12.3. Docker Desktop was stopped. No environment restart or new live authority was allocated for this accounting.

## Actual live task and boundaries

The original live Calc task saved A1=317 and A2=529, with no other nonempty cells, under the independently scored terminal-workbook boundary. It used seven public requests, thirteen primary commands, five original PNG presentations and two input programs. The terminal file oracle remains in the sibling frozen report. This known-family single construction success does not estimate general reliability or improve a comparison denominator.

`host-timing.json` replays hashes and the complete seven-call host timeline:

| Boundary/partition | Milliseconds | Interpretation |
| --- | ---: | --- |
| First send to last reply | 180018.869226 | Host lifetime subset, not setup-to-task completion |
| Requests outstanding, sum | 1019.610790 | Send to reply, includes input/release/capture where applicable |
| Presentation callbacks, sum | 7.455310 | Local callbacks; not provider receipt or model comprehension |
| Other disjoint host intervals | 178991.803126 | Caller orchestration, logging, scheduling and gaps; not isolated model thinking/wait |

| Attempt | Tool | Send to reply, ms | Send to callbacks complete, ms | Send to declared review, ms |
| --- | --- | ---: | ---: | ---: |
| 1 | observe | 171.587 | 178.955 | 14461.175 |
| 2 | clock | 6.688 | 7.631 | unavailable |
| 3 | dispatch | 473.349 | 476.214 | 20976.982 |
| 4 | inspect target | 79.901 | 81.217 | 19175.963 |
| 5 | review target | 80.138 | 81.528 | 44420.125 |
| 6 | dispatch | 177.922 | 179.496 | 47640.802 |
| 7 | close | 30.026 | 30.944 | unavailable |

Declared reviews are caller assertions after presentation, not independent measurement of the first useful feedback or earliest semantic understanding. The first-send-to-transport-close endpoint is 181955.955398 ms, distinct from the partition above. This evidence directs attention to decision-turn orchestration before optimizing the input backend; it does not assign the remaining time to one cause.

## Source-backed model usage

`usage-whole.json` and the 24 exact retained rows in `actual-source-records.jsonl` cover allocation preparation/build/launch through the first post-terminal independent XLSX scoring read: 2026-10-01T19:11:17.515Z through 19:14:41.646Z (204.131 seconds). They include reader/scaffold authoring, original image tool turns, reviews, clock, close and cleanup. Earlier failed allocations, implementation/preflight, later auditing/publication/accounting are outside this particular window and remain separate costs, not zero.

Eight unique responses; source-reported model `gpt-6.1-sol`, effort `medium`:

| Usage field | Tokens |
| --- | ---: |
| Input | 1647267 |
| Cached input, subset of input | 1629056 |
| Uncached input | 18211 |
| Cache-write input | 0 |
| Output | 5103 |
| Reasoning output, subset of output | 995 |
| Total | 1652370 |

Whole shared-context usage, with chronological association, not provider-attested per-tool/image attribution. The total includes repeatedly supplied conversation context. Cost and price snapshot are unavailable (`null`); no billing savings inferred. The independent retained-source verifier passes normally and under Python `-O`. Full source-session path and boundary hashes are in the projection; only this caller's tool/usage rows were retained, without reasoning/chat text extraction.

`verify_image_handoff.py` passes normally and under `-O`: all five encoded tool-output images exactly match the frozen PNGs and have `detail: original`. The modal PNG is identical in commands 5, 7 and 9 (77589 bytes, SHA256 `4999b53fb2f493dd7e0d6ca06b1d53a47db007ce07ba423275733b1b4d7957d9`). This does not independently attest provider preprocessing or model perception.

## Recorded-reply integration gate

`replay_reviewed_images.mjs` uses the actual current `createInstrumentedRelayClient` and `createPrimaryExchange` over a fixture that demands the exact seven frozen transport requests and returns the frozen reply objects. The thirteen frozen commands run with automated review reasons explicitly labelled contract-only; they do not represent current model review. No GUI/model/input backend is attached and no task authority is inferred from historical timestamps.

| Option | Public request objects | Primary commands | Image callbacks | Reference markers |
| --- | ---: | ---: | ---: | ---: |
| reuseReviewedImages=false | 7 | 13 | 5 | 0 |
| reuseReviewedImages=true | 7 | 13 | 3 | 2 |

References for commands 7/9 identify current attempts 4/5 and the explicitly reviewed full-modal base attempt 3. Current inspection/selection metadata still reaches the text sink, including binding revision 2 after selection. The changed final PNG is presented in both arms. All original native reply objects, including full PNG data, remain retained. The fixture reserializes JSON, so cross-run equality is object equality, not historical JSON formatting equality. `verify_reuse.py` independently checks the exact current/base/review/image byte identities against each replay's retained files; normal and `-O` both pass.

A first independent audit wrongly required historical pretty-JSON and replay line-JSON byte equality and failed. It was corrected without retrying any GUI/task. The replay's original base-hash check was insufficient self-equality; the independent audit now verifies actual base/review/current files. See `reuse-audit-first-failure.txt`; no historical evidence changed.

The frozen live `read_stage.py` drops `presented_text`, including reviewed-image-reference markers. Enabling reuse while retaining that observer would conceal the reference. The next live path must display the current metadata and reference marker explicitly and offer the existing `presentOriginal` recovery on uncertainty. Marker identity does not authorize input, renew a lease, rebind a window or imply task success. This is a concrete integration readiness condition, not grounds for adding another caller framework or automatic recovery.

## Next evaluation and remaining milestone

A focused live pair may isolate existing reviewed-image reuse, with the same production path/task/environment/model/settings and explicit review boundaries; it must count actual delivered images, whole response usage, local captures, failure/repair and elapsed endpoints. Freeze allocation/order/repetitions/stopping conditions before it runs. The pair has NOT been allocated here, and the replay's 5-to-3 callback result is not its result. No token or latency reduction is claimed.

This small admission ablation is justified by the concrete repeated-image delivery and hidden-marker integration condition. It does not replace the #57/#56 strong-baseline versus optimized versus symbolic comparison: cold acquisition/compilation, repeated warm use, dependency invalidation, bounded repair, subsequent reuse, equal allowed evidence/verifier assistance and all-attempt accounting remain outstanding. Compiled continuation must use the same permitted online assistance as the baseline; no privileged scorer or weaker baseline is introduced. Endpoint/provider schema conversion, model delivery timing, monetary cost and human-tempo comparison remain unproved.

## Reproduction

From the repository, use the physical Node binary rather than the Volta shim when isolating HOME. Source usage replay and image/reference audits are read-only:

```sh
python3 runtime/results/primary-modal-accounting-01/verify_retained_usage.py
python3 -O runtime/results/primary-modal-accounting-01/verify_retained_usage.py
python3 runtime/results/primary-modal-accounting-01/verify_image_handoff.py
python3 -O runtime/results/primary-modal-accounting-01/verify_image_handoff.py
python3 runtime/results/primary-modal-accounting-01/verify_reuse.py
python3 -O runtime/results/primary-modal-accounting-01/verify_reuse.py
```

The recorded-reply generator refuses occupied directories; preserve its existing output rather than rerunning in place. Timing uses `runtime/integration_checks/host_timing.py` on the sibling `case/host`. An initial timing read found sparse-checkout materialization missing; the exact tracked sibling evidence was materialized, then read successfully. This was a repository read failure, not a runtime/task failure. No repository AGENTS.md was returned by tracked-file inspection; `rg` was unavailable in Ubuntu and Git file inventory was used instead.
Local regression check: the existing production relay-host, primary-caller and primary-exchange suites passed 61/61 tests on Node 24.13.1; see local-host-tests.txt. This scope covers those composed host layers, not the entire runtime or provider endpoint conversion. No runtime production source changed in this report.
