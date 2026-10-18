# A03: bounded crop context replay

Using the exact A14 proposals on five frozen screenshots, the raw model crop, clipped to the runtime's 96-pixel maximum, is refused as flat in all five cases. A14 requested an interior crop that excludes border and label; expanding that rectangle by a fixed four pixels and clipping it to a 96×96 window centered on the proposed field point yields five valid fresh handles. Each resolves to its proposed point. Replacing the exact padded region with uniform pixels causes all five handles to return `MISSING`.

This is offline patch-identity evidence, not semantic grounding or task-effect proof. The full A14 crops are too large for the handle API and the initial size error is preserved. No code in the runtime changed; no model, GUI, or input was used. See `PLAN.md`, `INPUTS.json`, `RESULT.json`, and `out/UNBOUNDED_CROP_STOP.txt`.
