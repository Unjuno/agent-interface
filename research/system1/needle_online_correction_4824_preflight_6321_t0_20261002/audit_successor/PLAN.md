# #6321 generated-data audit successor

Allocation: `NEEDLE-ONLINE-CORRECTION-4824-DATA-AUDIT-SUCCESSOR-20261002-01`.

## H / T / D / C / U

**H.** An independently implemented, one-shot auditor can validate the already-generated immutable #6321 preflight data directly, without invoking its generator, failed wrapper, or first auditor. This specifically recovers the missing auditee-process receipt while preserving the original wrapper STOP.

**T.** Input is exactly `results/preflight-01/data.json`, SHA-256 `dad06f71a4a7acfd4ce110852ce5ee82f5e2ce654e1cf0f1d4401106f2edd188`. Candidate/generator invocations 0. New independent audit source and input digest are frozen before one network-disabled, CPU/memory-bounded OrbStack invocation using the cached immutable Python 3.12 image. Auditor invocation 1; retry 0. It may not import or execute `make_data.py`, `audit_data.py`, or `run_preflight.py`. Output path must be fresh. No model, optimizer, GPU, CUDA, GUI, network, or WSLc.

**D.** `PASS_DATA_AUDIT_SUCCESSOR_SCOPED` only if the immutable input hash matches; three exact seeds, 984 rows, all declared split counts, target labels, lineage, feature/ID uniqueness, within-role split disjointness, per-split bit balance, and seven corruption rejections reconcile; output records exit 0 and no errors. Any issue is FAIL/HOLD/STOP without retry.

**C.** This validates generated training/evaluation labels and split construction only. It does not validate a model, adaptation, skill routing, retention, or any CUDA behavior.

**U.** The original preflight remains `STOP_RUN_RECEIPT_POSTPROCESS_KEYERROR`; this successor does not rewrite it to PASS. GPU/window eligibility and all formal #6321 outcome thresholds remain untested.

Frozen audit source SHA-256: `874cec68c4c6f70ffb3d0b685c3b08fc86c4ec153fc3e0250b79a07d26bfe97c`. Frozen input SHA-256: `dad06f71a4a7acfd4ce110852ce5ee82f5e2ce654e1cf0f1d4401106f2edd188`. Image ID: `sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b` (`linux/arm64`, already cached). Main at freeze: `093b39fdab8d8cd04c422f8d9956deef1b40a692`.
