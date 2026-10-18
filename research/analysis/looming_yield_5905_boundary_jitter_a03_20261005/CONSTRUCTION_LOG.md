# A03 construction log

- A01 stopped at its original exact-main gate; A02 separately stopped after
  freeze when main advanced from `cd3a410a...` to `f44c5f57...`. Both have
  formal candidate/auditor counts 0/0. A03 is a new allocation and seed.
- The A09 historical FREEZE/SHA256SUMS candidate/auditor hashes disagree with
  the current-main bytes at those A09 paths. A03 pins the actual bytes freshly
  and preserves the discrepancy; it does not claim historical hash continuity.
- The A09 image digest was absent locally. A03 uses a separately inspected,
  cached Python 3.14.8 Linux/arm64 image digest and does not pull an image.
- A02's mount-smoke on this exact image passed with candidate/auditor 0/0.
  A03 repeats a path-local preflight before its own freeze.
- The first local A03 construction-test invocation exposed a wrong parent path
  in the generator wrapper; no candidate/auditor ran. The package was placed at
  an additive sibling path and the wrapper now resolves A02 explicitly.
- Local tests are construction gates, not TTC/simple-cue scientific outcomes.
