# Frozen execution environment

- Host: macOS arm64; the host-side auditor uses the Python 3 standard library.
- Candidate runtime: locally cached Node image by digest `node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80`; preflight identified Linux/arm64 and Node `v26.10.0`.
- Runtime: OrbStack Docker Engine `29.4.0`, Linux/arm64.
- Candidate limits: no network, read-only root, all capabilities dropped, no-new-privileges, UID/GID 1000:1000, one CPU, 256 MiB memory, 32 PIDs, 16 MiB no-exec tmpfs, read-only source/input mounts, one dedicated writable result mount.
- Candidate image is neither pulled nor rebuilt. Docker pull policy is `never`.
- Candidate performs PNG parsing/encoding and JSON payload accounting only. There is no OCR, model, browser, GUI, user input, or task replay.
- Auditor is a separate host Python standard-library implementation under macOS `sandbox-exec` network denial. It reads only frozen inputs and raw candidate artifacts, then writes an audit receipt.

The general Docker image inventory returned a containerd blob-read error during intake. The exact cached Node image was independently addressable by digest and passed a bounded no-network construction smoke test; no storage repair, prune, pull, or build was attempted.
