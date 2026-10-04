# Native MCP suite on WSLc — allocation A01

**Disposition: `STOP_SETUP` (2026-10-04).** The first and only image-build attempt failed before producing an image. The runner and candidate container were not invoked, so this is not a test failure or a WSLc test-runtime result. The failed build was retained and was not retried.

## Frozen question and scope

This was the prospective experiment registered in #5085 comment 5974859562 for the execution gate in #3352. The source was frozen at commit `25700c9f68e9937fc1057a5da91d14c3971bb2b6`. The Dockerfile blob was `f1464e51c2cc4e493c439f93fc049ccfe6221590`; the native runner blob was `d70fa82b1b29c4a384a95348697431ec3d28d2a0`; and the required `requirements-native-mcp.txt` blob was `c2bd62fb8e00ef32764d35e46276536648b8aea5` (12 bytes).

The materialized source manifest contains 1,087 files / 5,474,485 bytes. Its entries were checked against their Git blob SHA-1s. A subsequent frozen-tree completeness audit localized the source-acquisition defect: the GitHub Contents listing used for `research/live_control` returned 900 file entries, while the non-truncated direct Git tree at the same frozen commit contains 1,957 files. The CI non-cone workflow selects files directly under that directory, so 1,057 selected files were absent from the materialized context; the required requirements file is one of them. Across all selected roots, the exact expected inventory is 2,144 files versus 1,087 materialized (all 1,087 matched their Git blob IDs, with zero mismatches or extras). The first build log reports the missing requirements path at Dockerfile `COPY`, before dependency installation.

## H / T / D / C / U

- **H:** The repository's pinned image and declared 54-module native integration runner can execute in a fresh WSLc container with source read-only and runtime network disabled.
- **T:** One `wslc build --progress plain` using the frozen Dockerfile and pinned base digest. The build exited 1 at the `COPY requirements-native-mcp.txt` step. There is no image ID. The declared one candidate invocation (`--pull never --network none --cpus 1 --memory 512M --user 65534:65534`) and separate candidate-result audit were not reached.
- **D:** Preserve the first build command, complete build output, exit receipt, exact frozen source manifest, remote requirement-file identity, and the independent saved-result audit. The audit verified all 1,087 materialized Git blobs, the runner/Dockerfile identities, the missing required context path, and absence of an emitted image/candidate. No retry or replacement was made.
- **C:** This outcome tests only source-context assembly for a WSLc build attempt on WSL 3.0.1.0 / kernel 6.18.40.1. It does not exercise the 54 test modules, a running candidate container, offline runtime networking, GUI/model/action behavior, or any resource cap.
- **U:** No WSLc-vs-Docker parity, speed or memory/OOM benefit, effective CPU/memory enforcement, runtime test result, or roadmap completion is established. The failed build is not evidence that WSLc cannot run the suite.

## Retained evidence

- `source-files.json.gz` — compressed JSON manifest of the path, Git blob, and byte size for every materialized source file. Decompress to recover `source-files.json`.
- `source-tree-audit.ps1` — rerunnable comparison of the frozen CI source selection against Git tree objects.
- `output/source-tree-audit.json` and `output/source-tree-missing.json.gz` — supplemental, non-retry audit from the frozen Git tree, including the 1,057 omitted selected paths and blob identities.
- `remote-requirement.json` — independent GitHub Contents API identity for the required file at the frozen commit.
- `audit.ps1` and `output/audit.json` — independent audit implementation and saved audit result.
- `output/build-command.json`, `output/build.log`, and `output/build-exit.json` — first build command, complete output, and terminal exit receipt.
- `SHA256SUMS.txt` — SHA-256 custody for the published package files.

The allocation is terminal `STOP_SETUP`; no WSLc container from this experiment was created. A materially useful retest requires a new successor allocation and a separately verified complete source context. This record does not authorize that retest or change any predecessor result.
