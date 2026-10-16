# Measurement freeze

Task: INKSCAPE-SELECTION-BOUNDARY-20260916-013; Issue #333.
Immutable base: 3c6f07f0660aee854d6b2d2d0f525fd9f451de68.
No measured case has run at publication of this file.

Canonical SHA-256 hashes (the first run_case token in Issue comment 5691381864 contained a duplicated substring; its inline correction and this table give the correct 64-digit value):

| File | SHA-256 |
|---|---|
| prereg.json | 2512b200a3a395db6bf33ea0e65fac38401e9a1eaf672bb3864b08776a632990 |
| run_case.py | b3b1fbc27e5d7e160ba76fd0a3803a5b9e6766b5aace1632e98abbef09545e51 |
| run_block.py | 3819745b36cf11cb284ba00ba83baa5a877a61f8f442c3857f2d23618350e7fd |
| audit.py | bf9d1d831512738078b3a6dfafe7f29e9b684fad960178ef5d6f6e6d926fc654 |

Exactly 20 serial first cases, five per scenario, random.Random(33320260916).shuffle. Ordered scenarios: A_B_A, switch_to_B, A_B_A, unrelated_pointer, switch_to_B, stable, switch_to_B, stable, switch_to_B, unrelated_pointer, A_B_A, unrelated_pointer, switch_to_B, stable, stable, stable, A_B_A, A_B_A, unrelated_pointer, unrelated_pointer.

Fresh unmodified Inkscape 1.4; private profile and Xvfb 1100x800x24 per case. Validate visible selection A using the unchanged upstream scorer, construct a 2000 ms Lease bound to observed focus, apply only the declared OS selection change, then one Right press via unchanged InputOwner v10. Nominal dwell 20 ms. Diagnostic pre-edit capture is not consumed by admission. Ctrl+S persists the SVG for independent geometric scoring.

Expected +2 SVG user-coordinate units, tolerance .001, no change to rectangle y/width/height and exactly A/B. Stable/unrelated/A_B_A should move A alone; switch_to_B is expected to demonstrate wrong-target B movement. This hypothesis is not a production failure-rate claim. All cases require verified release, empty keymap/buttons, unchanged focus, admission before expiry and normal app exit. Stop on infrastructure/source/release failure; do not retry or extend.

One unsupported startup-option failure and four successful construction cases are retained separately and excluded. No model/game/custom application endpoint. Source and prereg bytes will be retained with results. This freeze does not authorize another worker or shared runtime mutation.
