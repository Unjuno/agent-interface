# Issue #4580 formal result

Status: `PASS_ROLE_SKILL_ROBUSTNESS_SCOPED` (narrow, synthetic role-skill reloadability study; not a general-purpose skill or model-quality claim).

- One frozen formal orchestration, 10/10 seed builders succeeded, zero retries, tuning disabled.
- All 20 isolated loader runs (two per seed) returned zero and accepted the corresponding package; package hashes were unchanged before, between and after loading.
- Independent audit recomputed held-out accuracy for roles A/B/C on 4,096 rows each. The minimum across all 30 role/seed cells was 0.90283203125 (seed 2026092700, role B); every cell met the preregistered 0.90 threshold.
- Graph reload/generation progression and all preregistered negative controls passed for every loader.
- Runtime: pinned local CPU-only Docker image, no network, read-only root/source/package, 1 CPU, 2 GiB RAM, 64 PID limit. PyTorch emitted a missing-NumPy warning; the frozen runner and loader did not require NumPy and no dependency was installed.
- The first audit invocation exposed an auditor/report schema mismatch (`runs` vs `seeds`, image ID location); it failed closed and its output is retained as `AUDIT_INITIAL_FAILURE.json`. No training was repeated. A separate post-run auditor adapted a temporary copy only, preserved frozen source and raw report, and independently audited all preserved raw seed evidence successfully.

Raw evidence remains locally under `outputs/formal01/seed-*` and is packaged losslessly in `outputs/formal01/bundles/seed-*.zip`; `bundle_evidence.py` regenerates these bundles and `EVIDENCE_MANIFEST.json` records SHA-256/byte counts. GitHub receives the frozen source, formal report, audit records, bundle manifest, and this summary; compressed binary evidence bundles remain in the local task workspace because the connected GitHub file API accepts UTF-8 text only.

This result supports only that this frozen synthetic pipeline produced reloadable role-skill packages meeting its specified competency and graph-control checks under the pinned CPU container. It does not establish online/runtime learning safety, real task transfer, or general agent capability.

