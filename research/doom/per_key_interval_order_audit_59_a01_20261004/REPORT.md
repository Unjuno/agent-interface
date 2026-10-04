# Per-key adapter interval ordering audit

This audit tests whether the V39 per-key receipt projection rejects internally valid input-edge records whose monotonic sampling brackets contradict the claimed DOWN-then-UP order.

## H/T/D/C/U

- **H:** `input_edge_receipts` at PR #7602 head `76886c5cc41ef801bf1d0cb153b1dabf444d9127` should not label an adapter pair complete when the entire `up` interval precedes the `down` interval. The status is a classification of sampled X-server keymap edges, not application receipt or task benefit.
- **T:** AST-extract the exact `input_edge_receipts` function from the pinned controller snapshot and run three synthetic pairs with matching program, step, key, token, owner, actuation ID, confirmed classifications, and authority-free fields: ordered DOWN `[100,110] ns` / UP `[200,210] ns`; overlapping DOWN `[100,200] ns` / UP `[150,250] ns`; and reversed DOWN `[200,210] ns` / UP `[100,110] ns`.
- **D:** The ordered pair should remain paired. FAIL the source if either the reversed pair or the temporally ambiguous overlapping pair is returned as `adapter_edge_brackets_paired`; retain all three cases in a repair regression.
- **C:** A malformed or reordered evidence record is not evidence that the retained experiment produced bad measurements. The live bridge may serialize valid events in temporal order; this audit only checks the projection’s own validation contract.
- **U:** Synthetic static counterexample only. It does not measure X11, physical key dwell, game consumption, controller behavior, or task effect.

## Result

The pinned function returns `adapter_edge_brackets_paired` for all three interval relationships, including reversed and overlapping brackets. It validates each interval's shape and checks matching actuation identity, but the completion predicate does not compare DOWN and UP interval order. The exact source snapshot, fixture, and raw reproduction are retained under this directory. Run `python source/audit.py` to reproduce; it exits nonzero if the pinned source changes or the reversed-pair finding no longer reproduces.

The required correction is to fail closed unless the two sampling brackets establish DOWN-before-UP, with regressions for reversed, overlapping/ambiguous, and correctly ordered brackets. This audit does not modify PR #7602 or assert any claim about its retained run data.
