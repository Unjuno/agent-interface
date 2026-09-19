# Target footprint reacquisition — local container freeze v1

Allocation: `TARGET-FOOTPRINT-REACQUIRE-20260916-01`
Publication base: `c6d195473be0aa876cc991093262494209c7971f`
Runtime dependency base: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245` from the hash-verified offline lab artifact.
Coordination: PR #326 successor; NOT Issue #327's post-selection paint-lag race.
Only this directory is writable. No shared runtime/workflow changes or existing formal MAP01 allocations.

## Question and conditions

Does bounded full-footprint retrieval preserve correct target deletion after reference-to-current relocation and reject same-color different-shape substitutes, missing targets and duplicate appearances where the prior 11x11 center patch is insufficient?

Three matched scene seeds/pans: (1841,-4), (1842,3), (1843,6). Five scenarios per seed: stable, moved_decoy, replaced_square, missing, duplicate. Two modes per scenario: center and footprint. Order alternates by seed-index plus scenario-index. Total 30 fresh Xvfb/Inkscape cases, sequential; one controller per disposable display. Both modes require two fresh target observations, 80 ms apart. All files are disposable fixture documents. No model calls, game state, or document oracle is available to the pixel controller.

Reference document provides one known target point and an observed footprint crop. Current document is a separately opened/rebound surface; references grant no input authority. Scene homography provides a coarse prediction only. Center arm checks the previous 11x11 max absolute RGB error <=8. Footprint arm searches within 120 pixels of prediction using full RGB TM_SQDIFF root-mean-square error <=20; a spatially distinct candidate <=23 refuses as ambiguous. Repeated candidate position must differ by <=2 pixels. Current observation age <=500,000,000 ns. Both then use ordinary InputOwner v10 click, Delete, Ctrl+S and verified empty release. SVG oracle runs after controller return.

PASS_SCOPED_CANDIDATE requires 15/15 candidate condition-correct outcomes and zero wrong-target deletion plus complete source/image/release audits. Stable/moved must delete only task-target and preserve other SVG contents. Replaced/missing/duplicate must issue no target pointer/Delete/Save and preserve exact file bytes. A completed mismatch rejects/holds the candidate. Infrastructure error aborts; all first results are retained and no same-ID retry occurs.

Development probes retained separately: normal center success; moved-decoy center deletes decoy despite zero center-pixel difference; footprint retrieves/deletes the relocated target. These are construction outcomes, not measured cases.

## Pre-run hashes

prereg.json SHA-256: `f8fe8c1ec63bf74274392f1ba789804f6832d6ad22a05389c92ad3ebabaf73d3`

| File | SHA-256 |
|---|---|
| resolver.py | 4a14bf804365cce7e1cff1d68e0373e58eb60e2cd50a7a23d78924906a0efd4b |
| controller.py | bd85fdff4da02a6eb5fcb5787be5f8a582bd7ef885c9239f69940bfa1357bf8a |
| run_case.py | ba48ef390a527382022cf81c2f2a6eaf176b695866b6a9ba2e2fae4a04fac5bf |
| run_block.py | a6b8c22fb8b15205987c141b079ba510a79d9f401a4f975ca314d7e21ac9711c |
| audit.py | ad5869dad1673e1eb48b878e01a822aabd1fff64fb04818fe0a8821d3c0187ce |
| test_resolver.py | 3625affdcb7708248bce15fa564d4713c9844c9438e093865470f5ba4bda642f |
| common.py | 0fd76e82c9bbdb0d560b2f04ae87d463ca48596f93597368dc64ba256f58a4f4 |
| reference_controller_v3.py | a1ca939f20da784e983373ed35284c8d0a92fe93ed10d340874f67468ebcdf66 |
| oracle.py | 6456f170d708a65ab1b3b895503a9389298790b83357466318cf5edbce4b63bb |

Eight deterministic resolver tests and py_compile pass before allocation.

## Limits

Full appearance is not semantic identity. Hidden same-appearance replacement, post-click selection interference, scale/theme changes, and targets beyond the search radius are not solved. The fixture is development-authored, not general model grounding. This measures task correctness, not causal latency superiority, model capability or MAP01 clear. Both clocks and input path are local Linux/X11; no hard-real-time guarantee.
