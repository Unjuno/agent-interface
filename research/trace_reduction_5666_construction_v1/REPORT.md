# Construction report — #5666

- Local command: `python work/issue5666_trace_reduction_t1_construction.py`
- Runtime: Windows host CPython 3.12.10; no Docker/model/GUI/network/input.
- First invocation: exit 1 at the one-minimality assertion due to an incorrect self-comparison after `noise` was already absent.
- Repair: enumerate deletion of each remaining node.
- Second invocation: exit 0; 6-node original -> 5-node synthetic reduced trace; same frozen `WRONG_TARGET_EFFECT` fingerprint. Exit-code-only deletion of `grant` or `release` rejected as a different typed failure.
- Local source SHA-256 before publication: `e3c9dca5df49d395c9f5203a228e96b50c1de23fd0ed0ee7eb45d7d12c732c67`.
- Printed-result canonical JSON SHA-256: `0c22e5f489216dfe8b81d02aa763a7df62aa5561b0cf63aaf570270373ec89d8`.
- No independent raw-only audit, no actual reducer search algorithm, no sandbox replay, no real failure, and no T2.
- Decision: `CONSTRUCTION_CHECK_ONLY`; T0 `HOLD_NO_REPLAYABLE_FAILURE` unchanged. No METHOD_PASS, live efficacy, causal attribution, or safety claim.

See [Issue comment](https://github.com/Unjuno/agent-interface/issues/5666#issuecomment-5922299325).
## Construction correction v2

After publication of v1, review exposed an inadequate `legal()` predicate: it accepted required nodes regardless of order. V2 requires the reduced trace to be a duplicate-free subsequence of the original, with no unknown nodes, and adds a negative control for `act` before `grant`. Host CPython 3.12.10 invocation exited 0. V2 local source SHA-256: `721c951b8c1decd4f3e2e359e9c0f1507b3778d70c2dc5367a88687f5a051152`. V2 canonical printed-result SHA-256: `df503bb1b4cb810d229c89b8b42bb1d3100db49c57e5105193424455f285dfbf`. V1's limited scope and first construction assertion error remain documented above. No independent auditor, container, actual search algorithm, or real trace replay has been added; decision remains `CONSTRUCTION_CHECK_ONLY`.
