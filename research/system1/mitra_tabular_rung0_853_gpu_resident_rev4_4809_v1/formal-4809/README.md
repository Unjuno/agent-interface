# Mitra-v2 resident CUDA inference — rev4 successor (#4809)

This package prepares one local RTX 3080 inference allocation under the dependency closure verified in #4800. It preserves #853's CPU STOP and the exact-lock STOP from #4745. No model, fit, prediction, or GPU call has occurred in this package yet.

## H / T / D / C / U

- **H:** one direct `MitraClassifier` on the pinned CUDA stack can keep its sole trainer resident and answer 1,024 sequential single-row queries plus 16 repeats with the frozen six-class ABI, zero optimizer steps, no checkpoint-scale query rereads, and warm p95 below 500 ms.
- **T:** exact #853 checkpoint/config/model card and support/query fixtures; AutoGluon 1.6.3; Python 3.11.10; Torch 2.5.1+cu121 / CUDA build 12.1; local Linux/amd64 Docker image `sha256:01ea4e60b03e8a7d48644d0dce596bd2e42ab3815fdc52b0c7a6d4cbcf757dac`. The only environment addition is the five hash-pinned #4800 rev4 packages. Runner/auditor hashes and all raw construction logs are pinned in `formal-4809/src/FREEZE.json` and `formal-4809/construction-manifest.json`.
- **D:** CPU/offline construction: direct `MitraClassifier` import passed; independent auditor/STOP tests passed 8/8. This establishes package/import and audit readiness only. Formal GPU observations remain zero.
- **C:** one `--gpus all` formal container, network disabled, source/model/inputs read-only, 1 CPU, 4 GiB RAM, 128 PIDs, one fresh writable output path. Before launch the runner requires fresh GitHub/task collision evidence and checks that only explicitly allowlisted containers (including the unchanged Ollama container identity) are running.
- **U:** one pinned small model and one synthetic 8-feature / 6-class support/query fixture on this RTX 3080. No accuracy, calibration, safety, fine-tuning, or product claim.

## Exact inputs

The frozen fixture files remain unchanged on main at `research/system1/mitra_tabular_rung0_853_v1/support.csv` and `queries.csv`. Their expected hashes are in the freeze. The model snapshot revision is `edada0d20759c58ada8c8605c25f22f6e98ea5f0`; the 302,717,904-byte weight file is SHA-256 `5ffab0e2cf52f61c5b7c7eb1e8542996736d1023a0212190cc09abc2119a1e09`.

The formal image is built from the pinned local CUDA base with `--pull=false --network=none`. It installs the unchanged 59-distribution #4745 lock plus the five rev4 additions from a locally hash-verified wheelhouse. The package archives are not duplicated here; source URLs, hashes, sizes and license evidence are retained under #4800 / PR #4808. Wheelhouse reconstruction/acquisition must finish before the offline build and must match its manifest exactly.

## Formal status and run rule

Issue #4561 still has an open deterministic-CUDA allocation whose latest result is CPU-only construction; its owner has been asked whether a formal GPU launch is still reserved. The shared RTX 3080 currently reads 0 MiB, and the only running container is the pre-existing Ollama service. Do not invoke the model until #4561 and active Codex-task ownership are cleared and a fresh collision evidence JSON is recorded. `formal-4809/src/run-formal.ps1` refuses to start without that evidence, exact source/input/model/image hashes, idle RTX 3080, and unchanged allowlisted containers. Its synthetic unresolved-collision control refuses to start before creating any output path or formal container. One formal invocation only; it preserves RESULT or typed STOP, the process log, container state, and independent CPU audit.

The prior #4745 runner's STOP path incorrectly named its old allocation. That preformal-only error-attribution defect was corrected here, with matching #4809 result/STOP schemas and synthetic mutation controls. The scientific procedure and thresholds remain unchanged; the historical #4745 files remain untouched.
