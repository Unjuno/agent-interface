# Empty event-index compaction fast path

- **Status:** Merged and registered in hosted native regression CI.
- **Source:** Issue [#8244](https://github.com/Unjuno/agent-interface/issues/8244), related to #3544.
- **Idea:** For finite acyclic JSON trees, after strict root encoding succeeds, skip descendant traversal when the event-reference index is empty while preserving the deep-copied subtree and encoded receipt bytes.
- **Outcome:** Merged [PR #8245](https://github.com/Unjuno/agent-interface/pull/8245) adds the four-line empty-index fast path and one shared native-CI suite registration. Hosted execution recorded all 12 focused methods, 552 protocol tests, 205 harness tests, and shared status PASS on a synthetic PR merge. This confirms regression inclusion for that tested combination; it is not a new timing measurement, product-performance result, or permanent artifact-custody claim.
