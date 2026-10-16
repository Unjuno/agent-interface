# Validate compiled GUI macros under environment interleavings

- **Status:** Unverified finite-method successor.
- **Source:** [Issue #8869](https://github.com/Unjuno/agent-interface/issues/8869), successor to #7827, #8592, and #8663.
- **Idea:** Test whether a compiled macro preserves its declared semantics when the environment changes independently between source-level steps, beyond validating a frozen source/target pair.
- **Prior evidence:** #7827 A05 reported a method-scoped result for its frozen finite source/target model, while #8592 studies bounded schedule exploration. Those results do not establish correctness under external environment interleavings.
- **Boundary:** No experiment, runtime integration, or live GUI result is reported for this proposal. Keep earlier results and their review history unchanged.
