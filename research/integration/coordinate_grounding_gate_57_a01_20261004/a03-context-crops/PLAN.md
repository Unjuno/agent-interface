# A03: bounded context around model-proposed field crops

## H — hypothesis

The 24×24 center patch used in A01/A02 refuses flat field interiors even when the proposal lies on a visible field. The A14 model crop coordinates may become usable if a fixed 4-pixel margin captures the field boundary, provided the handle region is clipped to the runtime's 96×96 limit. For these retained observations, the padded handle should resolve at the proposed point; a changed region should resolve as missing.

## T — frozen test

Inputs are the exact five A14 task screenshots and answer JSON blobs from PR #7353 head `e8f7c02cb98d849312a4889fa4d52ec424088732`, with source Git blob IDs and SHA-256 in `INPUTS.json`. The screenshots are the same verified images in sibling A02; no duplicate copies are added here.

`value_crop_xyxy` denotes the model crop's half-open x/y endpoints. A14's task prompt explicitly defined this as the field text interior and instructed the model to exclude the border and label. The raw case clips that rectangle to a 96×96 window centered on the proposed field point. The candidate case tests a separate post-model adaptation: expand the crop by exactly four pixels to include visual context, then intersect it with the same 96×96 centered window. Each region is minted against source sequence 1 and resolved at sequence 2 on identical pixels. For the change check, exactly the padded region is replaced by white pixels before resolution. All calls use identical focus, surface, and geometry bindings. The runtime implementation is unchanged.

## D — result and decision

The exact A14 crop without context is flat and refused on all five cases (0/5 handles), although the proposed points are visible in the fields. With four pixels of context, all five bounded patches pass mint and resolve to the exact proposed point (5/5). All five region-replacement controls resolve as `MISSING` (5/5), and no input dispatch occurs. The 96-pixel dimension bound is respected. Directly minting the full model crop first STOPped because A14 crops exceed the runtime's 4..96 size contract; that failed attempt is preserved.

This supports retaining the four-pixel-context construction as a candidate for further testing on this fixed sample. It does not qualify the method for live use: a self-matching exact patch is not semantic target evidence, and the mutation test is a synthetic changed-pixel check, not an application-level absence or effect test.

## C — limits and unknowns

The result suggests surrounding control context can recover flat interior targets, but the four-pixel margin is not optimized or generalized. No textured wrong-target or visually absent-target negative remains in the five screenshot set. The live admission/action race, target semantics, task effect, bounded recovery, privacy, and any token/time benefit remain unknown. No model, GUI, container, or input authority was used.

## Reproduction

From the repository root (fetch the frozen A14 source ref first):

```powershell
git fetch origin pull/7353/head:refs/remotes/origin/pr-7353
python research/integration/coordinate_grounding_gate_57_a01_20261004/a03-context-crops/extract_inputs.py
python research/integration/coordinate_grounding_gate_57_a01_20261004/a03-context-crops/run.py
python -m unittest discover -s research/integration/coordinate_grounding_gate_57_a01_20261004/a03-context-crops -p test_context_crop.py -v
python research/integration/coordinate_grounding_gate_57_a01_20261004/a03-context-crops/audit.py
```
