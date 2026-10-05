# A05 construction log

- A01/A02/A03 exact-main STOPs and A04 `FAIL_INTEGRITY_AUDITOR_INPUT_SCHEMA`
  remain immutable. A05 has a new path and seed.
- A09 historical candidate/auditor hash metadata disagrees with current-main
  source bytes. A05 pins actual source bytes anew and disclaims continuity.
- A09's pinned image is not locally cached. The already inspected Python
  3.14.8 Linux/arm64 image digest passed OrbStack mount preflight; no pull.
- A04 showed that A09 auditor expects the sealed-truth JSON root to be a list.
  A05 has a construction test asserting this exact envelope before freeze.
