# Validity-preserving reduction of interface traces

## Separate reduction methods: #5666 and #8878

### Frozen-trace delta debugging — #5666

#5666 asks whether causally closed pieces can be removed from one frozen replay trace while preserving its exact failure fingerprint and authority/effect/release constraints. Its current disposition is `HOLD_NO_REPLAYABLE_FAILURE`: the retained T0 input did not supply a failure that met the frozen replay precondition. Merged [PR #5669](https://github.com/Unjuno/agent-interface/pull/5669) integrates a construction-only synthetic reducer after preserving the first failed assertion and corrected invocation; no real replay or model/GUI/authority result followed. See [Issue #5666](https://github.com/Unjuno/agent-interface/issues/5666).

### Generator-trace reduction — #8878

**Status:** Open, unverified successor-method proposal; no reducer implementation or result claimed.

#8878 asks whether a recorded generator execution can be used to search for a different, smaller *valid generated execution*, rather than deleting events from one emitted trace and producing invalid candidates. The proposed output must preserve exact authority, effect, failure, setup, receipt, and release semantics. Generator validity alone does not prove semantic equivalence to the original failure.

This is complementary to #5666 and #8152, but not a replacement or retry. A future finite test should report valid-reproducer yield, size reduction, query cost, and independent failure-fingerprint preservation; it must retain authority/effect legality as hard gates. No live replay or destructive retry is authorized by the proposal. See [Issue #8878](https://github.com/Unjuno/agent-interface/issues/8878).

## Evidence boundary

Ordinary delta debugging, hierarchical reduction, and generator-execution reduction are established software-testing methods; their published results do not establish that Agent Interface traces have a suitable generator or that a reduced trace preserves an external GUI effect. Do not treat a smaller trace as causal evidence unless the frozen identity, environment, oracle, and exact failure fingerprint are independently maintained.
