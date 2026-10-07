# Issue #8319 A01 — crossed feedback × update-rule probe

This additive package tests whether the large feedback contrast reported by #8072 A02 depends on the candidate update rule used in each arm. It preserves the predecessor's outputs and treats both factors explicitly.

`FREEZE.json` binds the exact main base, source hashes, finite design, and one-shot invocation gates. Candidate and raw-only auditor are separate programs; the auditor does not import candidate code. The run is a native macOS standard-library simulation because this issue does not require a container. No isolation claim is made.

After execution, `results/candidate.json` retains all 400 cell rows and full development traces; `results/audit.json` retains independent reconstruction and mutation results. `REPORT.md` reports the four cells, paired within-updater feedback effects, updater effects, interaction, and scope limits. Do not interpret a pooled feedback contrast as general superiority.
