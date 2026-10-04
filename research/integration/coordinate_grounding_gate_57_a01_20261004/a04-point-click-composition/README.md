# A04: point-to-click-spec composition

A04 connects the retained A03 proposals to the point-derived command validator, a source-bound exact-pixel mint, fresh alias resolution, and an inert `pointer_click_target` action-specification sink. Five retained screenshots produce five accepted specifications. Each specification carries the original proposed point, the source-bound alias, selected box, point-relative offset, and exact patch digest. The actual `TargetHandleStore.mint` and `resolve_point` implementations are invoked.

The selected regions are centered on each proposal and fit within both the pinned validator's even 8–64 pixel dimension contract and the corresponding A03 context region: tasks 2 and 3 use 64×22, task 4 uses 64×40, and tasks 5 and 6 use 64×36. The pinned `model_point_target_v1.py` validator and derive functions are loaded from Git blob `45b3d57e7ef873e92e88107e7019d64376061216` after checking the object hash. The v33 session backend route is pinned for provenance and its source/fresh/focus ordering was inspected; it is not instantiated because its X11 session dependencies are unavailable in this environment. See `SOURCE_PINS.json` for that exact scope.

Task 3 negative controls show that the legacy fixed offset `[12,19]` resolves to `[230,409]`, so it is rejected before the sink rather than silently replacing proposal `[250,401]`. An unrelated alias returns `MISSING`. A changed source patch is refused before mint, while focus change, surface change, and a well-formed stale observation are refused by the actual fresh resolver. Every refusal leaves the action-spec sink empty.

This is offline pixel identity and composition evidence. The sink does not dispatch input; it grants no admission authority and proves neither semantic target correctness nor task effect. Model, GUI, and input dispatch counts are zero. The earlier A01–A03 evidence and r02 outcomes are not modified.

Run `python -m unittest -v test_point_click_composition.py` for the local tests. `RESULT.json`, `RUNS.json`, `SOURCE_PINS.json`, `INPUTS.json`, and `audit.py` retain the inputs, execution record, source pins, and independent result checks.
