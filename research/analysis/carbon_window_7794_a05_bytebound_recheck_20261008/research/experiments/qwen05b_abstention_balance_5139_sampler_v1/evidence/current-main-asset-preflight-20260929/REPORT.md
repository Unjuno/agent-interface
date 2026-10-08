# #5139 current-main and local-asset read-only checkpoint

Date: 2026-09-29  
Status: gate-3 partial preparation only; not a model experiment and not a formal freeze.

## H — hypothesis

The 11 upstream commits from the previous recheck base to current main do not alter the candidate sampler package. The exact model and tokenizer assets already cached locally remain identifiable by stable revision and content hashes, so they can be bound in a later formal freeze without loading the model.

## T — treatment

- GitHub MCP resolved current `main` to `708dec9bcd2bfb3ef597acf7bc1c8a02bcb96b01`.
- Compared previous recheck base `71f85380669795d21c668bcbc832ae896d0b6220` to current main: 11 commits ahead, 0 behind, 63 changed files, none under `research/experiments/qwen05b_abstention_balance_5139_sampler_v1/`.
- Read back the four source inputs from the current #5208 branch and matched local Git blob IDs: make_dataset.py `bae077ce`, protocol.py `d5073b51`, sampler.py `11286aec`, audit_sampler.py `06c97ca4`.
- Read-only hashed every file in cached Qwen/Qwen2.5-0.5B-Instruct snapshot `7ae557604adf67be50417f59c2c2f167def9a775`. Complete names, byte sizes, and SHA-256 values are in MANIFEST.json.

## D — result

The upstream main delta did not touch the candidate package, and all four branch source blobs matched their previously frozen identities. The cached model weight SHA-256 is `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`; tokenizer file identities are recorded in the manifest.

A read-only `nvidia-smi` snapshot reported RTX 3080 Laptop GPU, 16 GiB, 0 MiB used, 0%. This is host telemetry only; it is not a lease or a GPU test.

## C — controls

GitHub's main-vs-commit compare established the exact current-main SHA; a second compare enumerated changed paths. Source Git blob IDs were checked against local `git hash-object`. Local model/tokenizer files were SHA-256 hashed without importing/loading the model or tokenizer.

## U — limits and next gate

This does not complete #5139 gate 3: no fresh pinned-container identity/preflight, current formal dataset freeze, model/tokenizer load, CUDA call, LoRA fit, or independent formal-result audit occurred. It does not satisfy gate 1's named exclusive GPU/Docker lease or gate 4's owner/resource inventory. The latest #5085 comment explicitly prohibits further Docker invocation or inspection until exact coordinator assignment and owner/resource release are confirmed. Therefore no Docker action, container inspection, model load, or CUDA operation was attempted.

The existing GPU queue also records no #5139 lease. The idle Windows GPU snapshot cannot override that state. Preserve the existing construction STOP and result records; do not interpret this checkpoint as formal evidence or experiment success.
