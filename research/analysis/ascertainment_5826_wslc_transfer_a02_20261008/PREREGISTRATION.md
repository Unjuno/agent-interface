# #5826 A02 — WSLc container-transfer replication

Status: frozen before candidate invocation. This is a new, bounded runtime-transfer allocation. It does not alter, replace, pool with, or retry A01 host evidence or the failed OrbStack nested-container probe.

## H / T / D / C / U

**H.** The exact A01 oracle-blind candidate and separate auditor, with byte-identical frozen fixture and oracle, can execute in an isolated Microsoft WSLc container and reconstruct the same 18-opportunity / 72-row result. A runtime/image/source mismatch, candidate failure, independent audit failure, or corruption-control acceptance rejects transfer qualification.

**T.** One candidate invocation, one independent auditor invocation, and the five frozen corruption controls, all in WSLc with no model, GPU, GUI, OS input, or external effects. Source and fixture mount read-only; output is a new writable directory. Network disabled. Cached image only; no pulls. Exact commands:

```powershell
wslc.exe run --rm --name 5826-a02-wslc-candidate --pull never --network none --cpus 0.25 --memory 256m --mount "type=bind,source=C:/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/work/research-5826-wslc-transfer-a02/src,target=/src,readonly" --mount "type=bind,source=C:/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/work/research-5826-wslc-transfer-a02/out,target=/out" --tmpfs /tmp:rw,noexec,nosuid,size=16m -w /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/run_candidate.py --out /out/candidate.json
wslc.exe run --rm --name 5826-a02-wslc-auditor --pull never --network none --cpus 0.25 --memory 256m --mount "type=bind,source=C:/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/work/research-5826-wslc-transfer-a02/src,target=/src,readonly" --mount "type=bind,source=C:/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/work/research-5826-wslc-transfer-a02/out,target=/out,readonly" --tmpfs /tmp:rw,noexec,nosuid,size=16m -w /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/audit_result.py /out/candidate.json
wslc.exe run --rm --name 5826-a02-wslc-mutations --pull never --network none --cpus 0.25 --memory 256m --mount "type=bind,source=C:/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/work/research-5826-wslc-transfer-a02/src,target=/src,readonly" --mount "type=bind,source=C:/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/work/research-5826-wslc-transfer-a02/out,target=/out,readonly" --tmpfs /tmp:rw,noexec,nosuid,size=16m -w /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/test_mutations.py /out/candidate.json
```

**D.** `PASS_WSLc_TRANSFER_SCOPED` only if each invocation exits 0; candidate output reconstructs the exact frozen 72-row frame; auditor independently reports 9/12 oracle faults, missed-by-all `[F02,F04,F08]`, two-list estimates 7.5/7.0 against 12, preserves UNKNOWN and false reports; all five corruption controls reject; source/image identities match. Any mismatch is retained as the first A02 outcome without retry. The source auditor's legacy text label `PASS_METHOD_SCOPED_HOST` / `HOLD_CONTAINER_TRANSFER` is not rewritten; that label conflict is recorded separately and limits promotion unless a raw-only reconciliation establishes that only its cosmetic scope label is stale.

**C.** Windows host with WSL 3.0.1 / kernel 6.18.40.1-1; WSLc 3.0.1; cached linux/amd64 `python:3.12-slim`, repo digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, local image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`. CPU quota 0.25 and configured memory 256 MiB are requests only; no enforcement claim. No Docker Desktop/OrbStack daemon or image pull. This is distinct from #4917's 2-vCPU formal allocation and #5074's released Docker slot; it makes no use of either allocation.

**U.** This qualifies only one deterministic synthetic package and one WSLc image/host route. It does not establish effective memory enforcement, Docker/OrbStack equivalence, live ascertainment, hidden incident rates, runtime/product safety, or general WSLc reliability.

## Frozen inputs

Source package from PR #8389 head `6086879eac550ed0fa05175011d8d39602e55393`, based on earlier main `708ca59a8128f07fdb7e13a36704c6b2f79c9fb6`; current publication base is main `bfcc14e08fbfe5f2f04cd0237d13559e5d62538b`. SHA-256:

- `fixture.json`: `3114154c201a4d91f03607248fa5957ff2ba9f4be96b8c38f49840bbcbc3cd8d`
- `ORACLE.json`: `f61d807d62e48745891edd7bedcb2f189e96b9346125272bda1d864034be7bd9`
- `run_candidate.py`: `b146357926393bb2cc34f337f18d2579d37ed5c58ddd4663463840d8ede3a9da`
- `audit_result.py`: `14227d89d529a52f27d723a55c98d71fa15e631a61ac17928242eccd05315ba5`
- `test_mutations.py`: `a11cc9290500be46bdfdfcd0c74aaa1eddcf217d054cd95ab216e0ab7751c1ce`
- source `SHA256SUMS.txt`: `88f997673dd981c3e6d5fb78ff03b2fcb5c6ed236cdc74106a199366aff3b5c3`

No source or old raw result is modified. Candidate output destination `out/candidate.json` did not exist at freeze time.
