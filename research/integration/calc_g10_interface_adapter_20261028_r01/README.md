# Retained G10 graph to current fresh-reference adapter

Date: 2026-10-28 (Asia/Tokyo)
Main revision tested: 1de3dea2773a689ffb46e51e22f102e853402881

## Change and purpose

The retained G10 graph binds both sequential actions to one symbol and alias, a1_primary. The current fresh-reference guarded adapter intentionally rejects that graph instead of reusing an old target. A test had previously hand-added a second symbol in its fixture. This change makes that translation an explicit, strict adapter and routes the existing G10 FreshAdmission and native-caller tests through it.

The adapter clones the retained graph, preserves predicates, action meanings, expected effects and all state transitions, and only sets the runtime scope/surface plus gives the second action a distinct target symbol and alias. It accepts only the retained two-action enter_product contract, validates the result with the current compiled-GUI schema, and rejects extra transitions, changed effect contracts and duplicate aliases. It does not select targets, perform OCR, request model proposals, mint references, execute input, or score a live task.

## Evidence

The adapter uses the actual retained raw.json from calc-compiled-ocrlive-4d74/runs/compiled_ocrlive10, SHA-256 890c68f13e5fa8598bcbb2f456b8ee5319c584249c19492744a7c96f170014bf. Current G10 fixture and composition suites now exercise the adapter on the way into fresh admission and the Fake X native caller.

Windows CPython 3.11.9: normal run 13/13 passed; optimized (-O) run 13/13 passed. Complete output and exit codes are in normal.log, optimized.log, normal.exit-code and optimized.exit-code. The test includes adapter preservation/rejection cases, fresh-alias guarded execution, late proposal after verified release, and unknown-effect suffix stopping. source-identities.txt and support-source-main-blobs.txt pin current source IDs; support-source-sha256.txt records the local fixture source bytes. SHA256SUMS binds the packet contents.

## Scope limit

This closes an offline interface-shape handoff. The executor, application and transport are test doubles. It is not a new Calc task, a live X11/Docker/WSLc result, OCR/model accounting, or a matched efficiency comparison. A fresh live comparison remains gated by Issue #57 allocation/ownership and environment conditions.

## Reproduction

On a full checkout with the recorded test dependencies, run from the repository root:

    python -B research/integration/calc_g10_interface_adapter_20261028_r01/runner.py
    python -B -O research/integration/calc_g10_interface_adapter_20261028_r01/runner.py

This local checkout is sparse. For the recorded run, the five omitted-but-main-tracked live_control modules were supplied from a byte-hashed scratch source fixture by setting AGENT_INTERFACE_TEST_SUPPORT to that directory. The runner supports the same optional environment variable for a sparse checkout; in a full clone leave it unset. Exact resolved imports are shown in the logs.
