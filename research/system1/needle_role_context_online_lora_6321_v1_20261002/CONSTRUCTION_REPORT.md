# Construction report — Issue #6354

Date: 2026-10-02 UTC. Allocation: `NEEDLE-ROLE-CONTEXT-ONLINE-LORA-20261002-01`.

## Scope and disposition

This is construction/data-integrity evidence only. The pinned WSLc CPU container ran the 12 contract and independent-audit tests successfully and independently checked the frozen dataset. The RTX 3080 request was not a grant and expired; no model fit, CUDA operation, optimizer update, formal candidate, or candidate-output audit was run. Candidate/CUDA/update/formal-auditor/retry counts are 0/0/0/0/0. This does not answer the adaptation-quality hypothesis.

## Frozen inputs

- Base main: `93f0ee168051d4b4afcf381ea8e88245d89448f5`.
- Image: `pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`; inspected WSLc image ID `sha256:048a0de5d4322054f9d92a9dfd36f4cab1cd82dfbd1042ce2c51bd94f7e45d32`, linux/amd64, PyTorch 2.5.1, CUDA runtime 12.1.
- Dataset: `construction-01/dataset.json`, 121,749 bytes, SHA-256 `5865040abbc60d79f138e81bf7e06bf6f885e66b5e29c9810ea8f599bad77685`.
- Seeds: 2026100204, 2026100205, 2026100206. Independent cross-role vector overlap counts: 104, 102, 105. Same-role train/test disjointness, per-split balance, target labels, lineage and role-conflict probe were checked.
- Source/test hashes and runtime are in `FREEZE.json`; package checksums are in `SHA256SUMS`.

## Executed validation

Host: `python -m unittest -v test_contract.py test_audit.py` — 12/12 PASS.

WSLc CPU-only: `wslc run --rm --pull never --network none --cpus 1 --memory 2g --user 65534:65534 --mount "type=bind,source=<package>,target=/src,readonly" --workdir /tmp pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime python -B -m unittest discover -v -s /src -p 'test_*.py'` — 12/12 PASS. A separate CPU-only invocation loaded the exact mounted dataset and independent audit returned `[]`, with overlap counts `[104, 102, 105]`.

Dataset generation was executed once in WSLc CPU-only with read-only `/src`, fresh writable `/out`, network disabled and no `--gpus`; its exact hash is frozen above. WSL kernel warned that swap limit/cgroup accounting is unavailable, so the memory cap is without swap enforcement.

## Preserved pre-test launch errors

An initial WSLc test command used a read-only mount as a nonexistent workdir; runtime initialization failed before Python started (`mkdir /src/research: read-only file system`). A second command used `/tmp` but did not point unittest discovery at `/src`, so imports failed before test collection. A malformed PowerShell variable expansion was rejected before container creation. These are command/setup errors, not test or scientific outcomes. The corrected commands above passed; no optimizer or candidate code was invoked.

## Limits / next gate

No GPU allocation exists in the latest coordination record (#5085). The expired 01:15–01:45 request must not be inherited or rebooked. The formal candidate remains unexecuted. Proceed only if a new explicit authorization is later recorded and all exact current-main, image, source, data, output, owner and runtime gates pass. No result is promoted to Needle quality, real-time learning, runtime, safety, or product claims.
