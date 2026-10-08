# #5756 patch-leaving finite T0 — WSLc

Fresh additive successor allocation `SCENT-PATCH-LEAVING-5756-20261002-01`. This is separate from and does not alter #5756's earlier scent-search T0 or PR #5779. It tests only a finite synthetic subtree-leaving discriminator. Read `protocol.md` first. No GUI/model/GPU/network or live-agent claim.

Runtime: Microsoft's native `wslc.exe`, cached linux/amd64 `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, Python 3.12.14; CPU-only, network disabled, unprivileged user, 1 CPU/1 GiB. Formal frozen hashes and raw/audit records are in `FREEZE.json` and `evidence/`.
