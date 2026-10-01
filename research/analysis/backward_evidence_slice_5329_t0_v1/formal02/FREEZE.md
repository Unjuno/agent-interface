# Formal02 frozen allocation

- Issue #5329 freeze comment: #5924169406.
- Predecessor Formal01: retained unchanged as `STOP_PROVENANCE_OR_RUNNER`.
- Allocation: `5329-backward-slice-t0-20261001-02`.
- Main base: `24f6b7d5f9395105807f981d48db212e6692a6f4`.
- Branch: `research/5329-backward-slice-t0-formal02-20261001`.
- Runner SHA-256: `02D0767AF61080643FF6FF38BF68015F1B11724623BDD7F4ACF200EC98F087C9`.
- Auditor SHA-256: `DE947A87DF9D9C590F89867200AD930113E3A1B1FC9ED366F811CF9F586192BD`.
- Construction test SHA-256: `183931A941DFDAE73F158C3031EB32EC817A6AFFF56A25E109B1E9ED36CF131E`.
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Limits: network none; CPU 1; memory 256 MiB; pids 64.
- Formal output: `results/` (local `/out/formal02`). It was absent before invocation.
- Runner once, exit 0; independent auditor once after runner, exit 0; retries 0.

Pre-freeze AST and dangling-sentinel closure construction checks passed in the
pinned image. The formal runner and auditor each ran in a fresh network-disabled
container with source mounted read-only; raw was mounted read-only to the
auditor. Formal01 output was not used as Formal02 raw/audit input.
