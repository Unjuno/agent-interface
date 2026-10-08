# Supplemental T0 raw/audit archive qualification

This directory is a byte-preserving copy of the complete 12-file tree at
source commit `9f9c8cbf30025343e0d160e177c88d658655b03d`, originally published
under `research/analysis/constrained_interaction_testing_5330_t0_v1/` on the
closed, unmerged recovery PR #5358. It is kept at a distinct path because the
canonical path was independently populated on `main`; this archive must not
replace or be overlaid onto that current study directory. The Issue's current
main package remains the canonical discovery location.

The copied `REPORT.md`, `FREEZE.json`, `RUN_LOG.md`, `AUDIT_STOP_01.json`,
`raw.json`, and corrected `audit.json` retain the source branch's original
lineage and recorded outcomes. The candidate ran once. Its first audit stopped
because the frozen expected metamorphic count was 36 while the candidate
produced 27 from nine pairwise rows. A separate corrected, raw-only audit
consumed the same unchanged raw bytes and reported `PASS_T0_SYNTHETIC_DESIGN`
with four of four corruption controls rejected. No candidate rerun is part of
this archival copy.

Recovery checks for this copy:

- Raw SHA-256: `ad6be24a2bd8789ffae8c9ef632c829c47813dab6477be6a324dd3c77363fec4`.
- All 12 copied source/result blobs match the exact Git blobs at the source
  commit listed above.
- A fresh local raw-only audit reconstructed the archived `audit.json` summary
  and rejected all four recorded corruption controls.
- No candidate, GUI, model, container, GPU, network, or external-effect run was
  performed to produce this archive.

Scope remains the original deterministic, author-defined synthetic finite
model. Its enumerated hazard rules do not establish real-system failure
frequencies, GUI safety, or task/latency benefit. See Issue #5330 and PR #5358
for the contemporaneous status and delivery history.
