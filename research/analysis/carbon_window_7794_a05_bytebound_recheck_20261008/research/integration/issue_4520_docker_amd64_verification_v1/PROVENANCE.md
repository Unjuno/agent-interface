# Evidence recovery note — Issue #4520 local Docker linux/amd64 verification

This additive record preserves the original `DOCKER_AMD64_VERIFICATION.md` byte-for-byte from the closed, unmerged PR #4524. It records a local Docker Engine run, not GitHub Actions. It makes no claim that the tested historical source is identical to current main and does not change or reopen Issue #4520.

## Immutable provenance

- Original report path: `research/integration/host_broker_zero_exit_fix_v1/DOCKER_AMD64_VERIFICATION.md`
- Original report Git blob: `1d696e24c08438b36ce10d1da75889a4097f6518`
- PR #4524 report-bearing head: `14f86454d7d0ae58786f40747c72721e629d4535`
- Exact full-suite rerun head named by the report: `67c5da6cbda576fea44d57b7ee040830a17296b3`
- At both heads, broker blob: `24670929c734534c303a9b2ffebaa2b60d591385`; focused test blob: `39eb8a7484c97e13aee52ac91b93592c8f372fb0`.
- Current main after fix PR #4636 has broker blob `01fea5491d9a3df5ddd2496711ad0b69794932c7` and test blob `fb91bc6c52d92b82e3434a514a0ffe2a4c1ca4cb`; these differ from the historical tested blobs. Therefore this is historical, exact-head evidence only, not a fresh test of current main.

## Preserved result and limits

The original report states that both local runs exited 0 with 28/28 tests passed on Linux/amd64, using cached image `sha256:7e4a3b6f3917baa9f153b4dfd011a4ea528a3d200a7a3d274aa9479900ee7b41`, network disabled and read-only source. It separately scopes the earlier Python 3.12.10 host run and the ARM64 Docker result; no environment-equivalence, GitHub Actions, live-model, GUI, production-efficacy, or current-main claim is added here.

The source/implementation fix is already integrated by PR #4636. This PR only makes the distinct historical linux/amd64 evidence retrievable from main; it does not replace the failed Actions jobs recorded on #4524 or imply that those failures passed.