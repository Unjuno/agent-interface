# Issue #8604 T0 A03 — WSLc byte-reproducibility transfer

## H / T / D / C / U

**H.** The exact A02 frozen candidate, auditor and spec, when executed once each under the cached `python:3.12-slim` image in WSLc, will independently audit 24 cards / 120 keys and emit candidate and audit files byte-identical to the retained A02 host outputs.

**T.** Offline CPU-only WSLc container; no network, GUI, model, participants, human data, or action dispatch. Pin the locally cached Linux/amd64 image by immutable image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4` and registry digest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (tag `python:3.12-slim`). Mount this allocation directory only. Set `--cpus 1 --memory 512M --pull never --rm`. Run the frozen candidate exactly once to a fresh A03 output path, then the frozen independent auditor exactly once to a fresh A03 output path. Retain stdout/stderr, exit status, output bytes and SHA-256. Compare against A02's hashes as an independent byte-parity check; never write into A02.

**D.** `PASS_TRANSFER_SCOPED` only if frozen source/input hashes match A02, both WSLc CLIs exit 0 exactly once, the auditor reconstructs 24 cards / 120 keys with zero errors, and both output SHA-256 values equal A02. Otherwise retain the exact STOP/FAIL/HOLD and do not retry. No result supports human behavior or the Hick–Hyman hypothesis.

**C.** Matching output bytes demonstrate deterministic artifact portability for this finite Python CLI only. The image is cached and locally identified, not registry-digest authenticated; WSLc shares host resources and the memory/CPU flags are configuration, not evidence of effective enforcement. No container-vs-host performance or isolation conclusion is made.

**U.** This cannot validate participant comprehension, response latency, vignette realism, usability, cognitive theory, safety, runtime behavior, or product benefit. It does not authorize human-participant research.

## Custody

Successor to A02's host-only allocation, not a rewrite or retry. Source files are copied without modification and verified against A02 `SHA256SUMS`. A03 has separate outputs and an independent freeze/manifest. Construction tests run six cases normally and with Python optimization. Formal invocations: one candidate and one auditor; no retries or post-freeze changes.
