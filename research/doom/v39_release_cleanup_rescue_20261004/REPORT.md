# v39 release-cleanup branch rescue

## H / T / D / C / U

**H:** The old #7378 → #7385 → #7399 → #7395 stack contains useful release-telemetry evidence, but its runtime implementation must not replace the newer current-main implementation.

**T:** Compare the stacked branches and parallel #7386 construction repair with current main, retain unique experiment/results packages, run offline checks only, and document source-drift failures.

**D:** Preserve the split-step construction result, cleanup-overlap host/WSLc records, malformed-bracket follow-up, and one-shot T0 STOP. Do not replace mainline runtime code or broad integration tests.

**C:** The successful overlap evidence uses deterministic fake-owner/Xlib boundaries; the per-key T0 candidate stopped before Session creation or input. Neither is live gameplay, physical keyboard, application-effect, nor recovery evidence.

**U:** No candidate/container rerun, live allocation, or formal gate is claimed. The old saved-log auditors that consult current source files now report source-drift failures; original STOP/raw logs remain unchanged. The updated T0 candidate is not bound by the old freeze and must not be run until a fresh freeze/allocation exists.

## Lineage and integration decision

- PR #7378 head `fbed929f629dabaa9ae752019d0ee7151d4d2298` records the split-step release fix.
- PR #7385 head `90e65c932a8a487d9657713e5a243cba25125c4f` adds cleanup-overlap classification and a pre-start T0 STOP.
- Parallel PR #7386 head `341c333f33908852d3ff377c79d5100bb0e1ee91` repairs candidate network-receipt handoff and malformed-keymap audit handling; it preserves the original STOP and requires a new freeze before any future candidate run.
- PR #7399 head `f63f673538690fe6d6661a22d894cf1c061d3385` preserves terminal cleanup receipts.
- PR #7395 head `ece144c6c9304ffda03cb3d32beff06acdc986da` adds malformed release-bracket fail-closed checks.

The current mainline `research/doom/doom_typed_release_backend_v3.py` was subsequently evolved by commits `93c243ad80`, `bb3d1c93cf`, and `8f6d92cd2f`; current main also has the newer `doom_retained_input_backend_v4.py`. Main already retains a later owner-queue composition package whose saved audit covers cancellation and expiry cleanup races. Therefore these stale runtime files/tests were not overlaid. Four branch-only evidence paths were carried over; the T0 candidate/auditor construction files were then advanced with #7386, while the original freeze, STOP, and raw run receipts remain untouched. The pre-repair candidate remains retrievable from the preceding rescue-branch commit:

- `map01-v39-per-key-release-live-t0-20261004/`
- `map01-v39-release-cleanup-overlap-v1/` (including the #7399 extension)
- `map01-v39-release-cleanup-followup-v1/`
- `results/map01-v39-per-key-release-telemetry-port-v1/`

The latest observed `origin/main` is `f406e21e2430e40602d49dcd021e9a8365200430`. The intervening #7599/#7601/#7603 updates add evidence under separate paths and do not change these release-cleanup implementation/test sources.

## Revalidation on current main

- Updated #7386 candidate construction suite: 6/6 PASS; malformed-auditor mutation suite: 6/6 PASS under Python 3.12 normal and `-O` modes. The frozen T0 outcome remains STOP before Session creation; it was not retried. The updated candidate source differs from the freeze and is not authorized for execution until a new freeze/allocation is produced.
- Cleanup-overlap retained-log auditor mutation suite: 5/5 PASS. The package audit's current-source check fails because the current main test file no longer contains the historical `test_cleanup_inside_explicit_release_bracket_is_not_ordinary` case. The other retained-log checks pass; this is recorded source drift, not a rewritten historical PASS.
- #7395 follow-up auditor: all saved-log/source-pin checks pass except `all_adversarial_tests_present`, because the live test module has evolved since the stacked branch. Historical run receipts remain byte-for-byte preserved.
- Frozen SHA manifests were checked without rewriting them: package-local evidence hashes match, while entries pointing at the current root backend/test source differ from old pinned bytes. The updated T0 candidate also intentionally no longer matches the historical freeze. These are recorded source-evolution mismatches; the STOP and raw receipts were not altered.
- Current-main retained-input backend v3 tests: 11/11 PASS; v4 tests: 8/8 PASS. The typed v3 test command could not import optional Pillow in the available Python 3.12 environment (`ModuleNotFoundError: PIL`), so no result is claimed for that command.
- Cleanup-overlap auditor-mutation suite: 5/5 PASS in normal and optimized Python. The workspace index passes (159 directories); analysis index passes (670 directories).
- Whole imported evidence has one preserved blank line at EOF in `SPLIT_STEP_FIX_01_CONSTRUCTION.txt`; it was not normalized. All other scoped diff checks pass.
- No container or live X11 experiment was rerun. The earlier branch record says the OrbStack container preflight was blocked and records the first T0 candidate STOP.

These results preserve useful lineage while keeping the newer mainline implementation authoritative. The saved `PASS` labels in predecessor packages refer to their exact historical source trees, not to current-main source compatibility.
