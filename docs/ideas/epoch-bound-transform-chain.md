# Epoch-bound capture-to-input transform chains

- **Status:** A01 packages were non-conclusive; a separate exact-oracle A02 passed on a finite synthetic fixture.
- **Source:** Issue [#8185](https://github.com/Unjuno/agent-interface/issues/8185), with exact-oracle successor [#8201](https://github.com/Unjuno/agent-interface/issues/8201), in the #4323/#6684 transform lineage.
- **Idea:** Bind a captured point through source display/window/DPI transforms to the input epoch, rejecting stale or ambiguous mappings after display changes.
- **Outcome:** Read-only review found that two A01 packages did not establish the intended discriminator: one auditor reused candidate baseline refusals, and the other comparator refused multi-edge/uncertainty cases by construction and used authored expected points. The distinct A02 exact-oracle result in merged [PR #8211](https://github.com/Unjuno/agent-interface/pull/8211) audited 20 synthetic cases, rejected 11/11 invalid controls, verified the inverse-shear identity and 7→8→9 epoch path, and reduced false UNKNOWNs from 3/3 to 0/3 exact-safe composed cases. No native DPI, GUI, input, or task-effect result follows.
