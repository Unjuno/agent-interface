# Delivery provenance

The experiment source and fixture were frozen against repository `main` at
`2f36f501f11931e052dbc3fb0000a9200bff7f50`. The separate additive delivery
branch `research/observation-omission-8397-t0-a01-20261008` was created from
the newer `main` head `6dd1d62c49264832d0d7eb061395e467c529a34f` after a
concurrent merge. The fixture and Python modules are self-contained and import
no repository runtime code, so this delivery rebase does not change the frozen
experiment or its raw result. No files in `main` were modified directly.

The branch contains only the new `research/analysis/observation_omission_8397_t0_a01_20261008/`
package plus the required generated analysis-index entry and CI construction
test registration. The original Issue #8397 remains unchanged; its T1 empirical
allocation and parent-issue hypothesis remain open.
