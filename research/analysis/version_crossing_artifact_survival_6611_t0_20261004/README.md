# Issue #6611 T0 — version-crossing artifact-survival scorer

Finite no-model test of a scorer that keeps initial task success separate from
later-reader survival. It uses two synthetic routes with equal initial
significant properties and deterministic reader transformations, including
semantic loss, render-only loss, cosmetic change, open failure, and missing
dependency. It tests scoring sensitivity only—not real file-format
compatibility or long-term preservation.
