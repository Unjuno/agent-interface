# Calc G10 and current-main integration crosswalk (2026-10-27)

The earlier #57 search and two-cell/modal integration plan overlooked the archived #3311 Calc G01–G10 constructions. Current main contains the [literal-copy evidence package](calc_current_shared_3311_4d74_20261004/README.md). Historical statements inside individual reports that delivery was pending describe the time of those reports; their files are now present on main. Preserve those original statements.

## Existing evidence and distinct scopes

- [G03](calc_current_shared_3311_4d74_20261004/calc-guarded-integration-4d74/REPORT.md) records guarded input, stale pixel-reference refusal before emission, explicit repair and later reuse. One construction sequence; primary context/token usage unknown.
- [G08](calc_current_shared_3311_4d74_20261004/calc-compiled-digits-4d74/REPORT.md) records a held-out digit-recognition failure and censored second action. Do not retrain on or relabel that first outcome.
- [G10](calc_current_shared_3311_4d74_20261004/calc-compiled-ocrlive-4d74/REPORT.md) records two guarded Calc saves, three capture-time-bound graph observations, OCR of two rows and independent saved-XML scoring, under fixed geometry and font. Primary usage remains unknown; no same-model matched economic comparison follows. Source labels include inherited G09 wording, as its report explains.
- The newer `calc_compiled_method_v1.py` graph represents a different two-cell and modal-save workflow; its tests use supplied synthetic observations and targets. It neither replaces G10 nor proves an integrated live adapter.

## Pinned implementation versus current main

At current main as of this crosswalk, SHA-256 of the archived G10 source blob and current path was compared directly, without executing either or touching a live runtime:

| Source | Archived SHA-256 | Current SHA-256 | Match |
|---|---|---|---|
| `runtime/core_v1/compiled_gui.py` | `d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014` | `a00ca311ce80a9cc691f25b24569f95715f6051991b59578861f8d5b9b48d68f` | no |
| `runtime/guarded_x11_v1/bridge.py` | `0a0675709f2f2e7210ba92fb657c61e860ac1fef2126ef4006bf88699d556e71` | `153a65bd450b4903449f882bf1821f36c23578536db50e6c87c9aed87cfc4910` | no |
| `runtime/guarded_x11_v1/handles.py` | `b70e99aa0f7540c7c412b27e38c1fedc71ad257235e3a753ebe15e8e7f5849b7` | `b70e99aa0f7540c7c412b27e38c1fedc71ad257235e3a753ebe15e8e7f5849b7` | yes |
| `runtime/backends/x11_v1/backend.py` | `6ba5ea5d4e8fc797fc26a19879cffcfd00926606f53b0ef76fbff5f6b5f779db` | `7218eb2a2f80b7a09fcf355b718d97fb2c31b372346f014a334e948f132cac11` | no |

Seven G10 packet files (`compiled_ocr.py`, `effect_predicate.py`, `ocr_reader.py`, `saved_oracle.py`, `AUDIT.json`, `PLAN.json`, `REPORT.md`) match the sizes and hashes in `FILES.json`; this is not a complete package or raw-frame audit.

## Next integration decision

Compare the archived G10 guarded bridge, semantic recognizer and source-capture clock contract against current-main interfaces and the chosen task, including stale/unknown, releases and bounded recovery. Select and test a reproducible adapter based on existing qualified code when applicable. Then prospectively freeze the matched same-model cold/warm/invalidation/repair comparison, its all-attempt model/OCR/native costs and independent effects. A fixed offline method graph and an archived positive do not alone satisfy that comparison. No existing allocation or historical auditor is rerun by this crosswalk.

## Current-core offline construction check

A read-only fixture consumes the hash-pinned G10 raw interface, compact observations and terminal summaries and runs the current compiled core with inert admission, execute and effect callbacks. The unmodified recorded predicates reach two core transitions; mutations making the first effect unknown or stale stop before a second action. The fixture uses a deterministic simulated clock and reconstructed release fields; it does not run OCR, the original actor/auditor, X11, or the native bridge and cannot verify actual release, observation acquisition, or current-main live compatibility. Thirty-eight selected offline tests passed normally and with `-O`.

## Fresh-reference handoff gap

The G10 graph records one `anchor` symbol referencing `a1_primary` for both actions, while its custom live `admit_graph` minted and used `a1_second` after the first action. The current shared guarded adapter resolves each graph action from its declared symbol; it does not reproduce that custom remint. A test combines the retained G10 graph (with only synthetic scope/surface substitutions) with the actual shared adapter and a fake bridge whose original alias becomes stale after the first input. It stops before the second input. A separate modified-graph fixture with distinct aliases and a fake registry that supplies a fresh second alias reaches two transitions. Forty-two selected offline tests pass normally and under `-O`. Neither fixture mints a real alias, checks live pixels, proves semantic continuity, or verifies native release. A future integration needs a bounded fresh-observation/target-binding mechanism, not blind reuse of the old coordinate or an automatic remint from unverified evidence.

## Explicit post-action proposal binding

`calc_fresh_reference_v1.py` binds an externally supplied proposal to the latest bridge capture, matching digest, scope, binding revision, a post-action same-clock boundary and a 1.5 s capture-age limit before invoking the existing observational `mint_reference`. It checks revision/sequence/review/recovery again after mint and reports a possibly consumed alias on uncertain completion, without retry. A fake bridge backed by the real `TargetHandleStore` tests valid, stale, mismatched and changed-association cases; forty-seven selected offline tests pass normally and under `-O`. The bridge metadata and candidate semantics are trusted inputs; matching pixels/digest and time do not prove that the candidate is the intended target. The helper grants no input authority, does not automatically choose or repair a target, and is not yet connected to a live G10 controller or independently verified effect.

## Fresh-proposal guarded composition

An experimental G10-shaped adapter now composes the shared guarded `_Adapter` with the explicit post-action proposal helper. It requires distinct first/second aliases, a completed first terminal with verified empty release, a post-return capture and an explicit caller proposal; after observational mint it still delegates resolution, expiring admission and input dependency checks to the shared adapter. Wrong digest, changed binding, cancellation or missing proposal stop without a second input or retry. Fifty-two selected tests pass normally and under `-O` using a fake bridge, including actual `TargetHandleStore` tests for the separate helper. The proposal provider and semantic recognition are trusted callbacks; this composition cannot establish their correctness or enforce a deadline on a blocked callback. It is not connected to the historical G10 actor, and no live X11/Calc or independent task result is established.

## Optional bounded proposal wait

`BoundedProposal` provides a single-use wait around a trusted read-only proposal callback. It rejects late or cancelled replies and does not schedule a second attempt. An offline G10-shaped composition test verifies that timeout leaves one completed synthetic transition and no second input. Fifty-eight selected tests pass normally and with `-O`. This wrapper is opt-in: the G10-shaped adapter still accepts a bare callback, so users must explicitly supply it. A blocked Python worker may continue after timeout; callback side effects are not sandboxed, and copying inputs, cancellation callbacks, scheduling, native calls, physical release and process shutdown are not bounded by this mechanism. No live correctness or total deadline claim follows.

## Explicit bounded-worker entry

A separate `run_with_bounded_fresh_proposal` entry requires a fresh `BoundedProposal` and the same cancellation callback as the graph before any action. The caller retains the worker object to inspect a possibly still-running callback. Synthetic tests reject bare, reused or mismatched-cancellation workers before input, and exercise both a timely proposal and a timeout with no second input. Sixty-one selected offline tests pass normally and with `-O`. The older entry still permits bare callbacks; neither entry makes the callback a sandbox, stops a blocked Python thread, bounds native I/O, or proves live release/task success.

## Retained OCR input reconstruction

A read-only test pins the G10 raw JSON and OCR-attempt log hashes, verifies three original PNG digests and ROI RGB digests, reconstructs the seven retained OCR crop images at pixel level, and checks the attempts group by source frame as 1/3/3 with recorded outputs and timing. It was checked with Pillow 12.3.0; image resampling implementations may affect portability. Sixty-two selected offline tests pass normally and under `-O`. This neither reruns Tesseract nor independently establishes that its outputs are semantically correct, transferable, current, or associated with a new live action. No original allocation or auditor was rerun.

## Retained tri-state predicate in current guarded composition

An offline fixture pins the G10 raw bytes and archived pure `effect_predicate.py`, then supplies the recorded decoded values to that function in the current bounded-proposal/shared-guarded graph with a fake bridge. The recorded matching decode permits two synthetic transitions; an unavailable decode stops as `effect_unavailable` and a mismatched decode as `effect_failed`, before any second proposal or input. The 64 selected offline tests passed normally and under `-O`; the focused two tests were rerun after adding the source hash guard. No Tesseract process, original actor/auditor, real X11 input or Calc effect was executed. The fixture does not qualify OCR on new images, prove semantic target identity or establish live task success.

## Caller plus retained independent scorer, offline

A test connects the actual v3 caller to the current G10-shaped guarded composition using a fake bridge and simulated observations, then applies the hash-pinned original pure saved-XML scorer to the retained second FODS file. After two inert core transitions, matching expected values allow the outer test caller to succeed and a mismatched expectation makes it unverified. An unavailable first decoded effect stops after one transition and skips the outer scorer. The saved file predates the simulated actions and is used only as a fixture; it is not fresh post-action evidence. The test patches the compiled-core entry to use the guarded adapter and does not prove a production caller binding, OCR accuracy, native release, real task effects or economic benefit. Sixty-six selected offline tests pass normally and under `-O`.

## G10 guarded path through caller v3

A dedicated research entry now calls the bounded G10-shaped guarded adapter through the existing v3 caller, with a target-builder invoked on the final selected target, the shared compiled-receipt decision mapping, optional receipt publication and independent outer effect verification. The compiled mapping was factored out of the prior caller composition without changing its contract. Offline fake-bridge tests cover the final selected target, partial stop on unknown effect, matched and mismatched historical FODS scoring, and receipt-sink failure with a retained completed receipt. Sixty-nine selected tests passed normally and under `-O`. The saved FODS predates the fake actions; these tests do not establish live freshness or causation. The callback-defined target semantics, bounded native I/O, provider/model accounting, durable evidence, physical release, collateral scoring and an actual live comparison remain open. An exception before the guarded adapter returns may still leave no returned compiled receipt.

## Current guarded bridge and caller composition over Fake X transport

`test_calc_g10_native_caller_composition_v1.py` extends the composed path through the actual current `NativeHandleBridge`, X11 runtime session, shared guarded compiled adapter, bounded fresh-proposal worker, compiled core and v3 caller. Fake X supplies only transport and application-state changes. In the positive construction case, a click changes pixels under the first handle, the actual handle store returns `MISSING` for that old reference, a distinct reference is minted from the new captured frame, and two XTEST click sequences each return a verified-empty release; the outer effect callback is explicitly synthetic. In the changed/unknown-effect case, one action and its empty release are retained, the next action is not dispatched, proposal work is not started, and outer scoring is skipped. The 2 tests pass normally and under `-O`; the previous eight selected modules also pass 23/23 in both modes. This closes a composed offline adapter/runtime seam only. It does not run a live X server, Calc, OCR, provider/model, independent task-effect oracle, Docker, or the cold/warm/invalidation/repair comparison; the actual live and economic gates remain open.

## Core callback exception returned through G10 caller

The current branch adds a focused G10-v3 caller regression where the second bridge input callback appends a possible dispatch and then raises. The compiled core now converts that callback exception into a typed partial receipt; the caller returns `EXECUTION_INCOMPLETE / delivery_uncertain`, retains the first completed transition and unresolved second action, publishes the receipt once, and skips independent outer scoring. The eight selected G10 offline modules pass 23/23 normally and under `-O`. This closes the callback-exception-before-receipt case for ordinary exceptions raised inside compiled admission/execution callbacks. It does not prove persistence across process loss, cover fatal `BaseException`, establish live X11/Calc behavior, or close the cold/warm/invalidation/repair comparison. The prior broader wording above remains applicable to failures outside the core callback boundary.

## G10 historical cost coverage recount (2026-10-28)

The separate [read-only cost recount](calc_g10_cost_recount_20261028/README.md) verifies G10 source hashes and reconstructs recorded host/container, compiled-graph, native-program and all seven OCR subprocess timings without replaying its actor or auditor. Host elapsed is 29.933 s, container elapsed 26.556 s, graph elapsed 1.972 s, native attempts 0.569/0.566 s, and OCR subprocess intervals sum to 0.494 s. These are nested/different timing boundaries; they are not additive cost components or a baseline comparison. The original audit reports two saved effects passing, but the independent scoring timestamp is not joined to host elapsed. Primary model usage remains UNKNOWN; no additional benchmark model calls were made. This recount supplies useful local-cost coverage only; matched arms, model tokens/waits, end-to-end time to independent effect scoring, warm reuse, invalidation/repair, speedup and break-even remain unavailable.
