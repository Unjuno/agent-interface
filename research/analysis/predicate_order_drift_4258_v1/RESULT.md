# Formal result — Issue #4733

Disposition: **PASS_DRIFT_BOUNDARY_MAPPED** for this declared synthetic grid.

## H/T/D/C/U

- **H:** a cost/selectivity order frozen at the development distribution remains semantically exact but loses its cost advantage under enough probability-mass drift from early A rejection to late D rejection.
- **T:** one Docker invocation enumerated the full four-Boolean truth space (16 states) at 21 alpha values from 0.00 to 1.00 by 0.05. Predicate costs were A/B/C/D = 1/2/5/10; naive order D,C,B,A; frozen cost/selectivity order A,B,C,D. Mass 0.8 transferred between A-only-false and D-only-false strata; all-true retained 0.2. The container had no network, a read-only root/source, 1 CPU, 512 MiB memory and 32 PID limit.
- **D:** the first grid point where the frozen order's expected weighted cost exceeds naive is **alpha=0.70**. The independent raw-only audit reports `PASS_DRIFT_BOUNDARY_MAPPED`, errors `[]`, 336 rows, 21 distributions and 5/5 effective corruption controls rejected. Both orders match exact conjunction on every state.
- **C:** authored binary states/mass transfer, fixed deterministic costs and finite 0.05 grid; no asynchronous work or wall-latency measurement.
- **U:** synthetic sensitivity only; no arbitrary-drift guarantee, runtime order adaptation, real predicate/provider latency, GUI, authority, model utility or product claim.

## Selected points

| alpha | Frozen order expected cost | Naive expected cost | Frozen p50/p95 row cost | Naive p50/p95 row cost |
|---:|---:|---:|---:|---:|
| 0.00 | 4.40 | 18.00 | 1 / 18 | 18 / 18 |
| 0.65 | 13.24 | 13.84 | 18 / 18 | 10 / 18 |
| 0.70 | 13.92 | 13.52 | 18 / 18 | 10 / 18 |
| 0.75 | 14.60 | 13.20 | 18 / 18 | 10 / 18 |
| 1.00 | 18.00 | 11.60 | 18 / 18 | 10 / 18 |

Expected weighted predicate cost is an authored cost-unit calculation, not elapsed latency. The 0.70 result is a grid-resolved crossover, not a continuous threshold estimate. Row-cost percentiles are weighted across the declared distribution and are not end-to-end latency percentiles.

## Reproduction and provenance

Image: `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, Linux/amd64, Python 3.12.14; already cached locally, not pulled. Construction-only protocol tests passed 5/5 before source freeze; no formal retries, replacements or post-result tuning. The one formal Docker invocation exited 0 and emitted `PASS_DRIFT_BOUNDARY_MAPPED`, 21 distributions, 336 rows, first crossover 0.70, errors `[]`, and 5/5 corruption controls rejected. Post-result local CI initially attempted to write `__pycache__` on the read-only source mount and failed with `[Errno 30]`; rerunning with `PYTHONPYCACHEPREFIX=/tmp/pycache` passed byte-compilation and all 5 tests. This setup failure did not rerun or alter the formal allocation.

Exact formal invocation (host bind paths are from the execution machine):

```powershell
docker run --rm --name pred-order-drift-4258-20260927-01 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cpus 1 --memory 512m --pids-limit 32 --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\.agent-interface-docker-validation\predicate-order-drift-4258-20260927-v1\src,target=/src,readonly" --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\.agent-interface-docker-validation\predicate-order-drift-4258-20260927-v1\raw,target=/raw" --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\.agent-interface-docker-validation\predicate-order-drift-4258-20260927-v1\audit,target=/audit" --workdir /src sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 sh -lc 'python3 -B /src/run.py /raw/RAW.json && python3 -B /src/audit.py /raw/RAW.json /audit/AUDIT.json'
```

- `raw/RAW.json`: 186,739 bytes; SHA-256 `5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbbe0f28c7ec35e7d`.
- `audit/AUDIT.json`: SHA-256 `55b91ba52c5df69adef809dd1ce721dbb9f59d807dc4c64a83b7cecfa9a1a181`.
- Lossless `RAW_AND_AUDIT.zip`: SHA-256 `81f347c99c7461a210edf98437bd7f8ed298dd6f95070d0da4b447913d11a5c0`; published as base64 text at `RAW_AND_AUDIT.zip.base64` (SHA-256 `795f6a894959b2defc2bd0d006c89f858ada09c6bede92ae7f23d3adbc715910`). Decode it to ZIP before extracting; the original `RAW.json` and `AUDIT.json` hashes above apply to extracted members.
- `FREEZE.json`: SHA-256 `92f9957bc8350be1c0fbbaf9895ba3df59ed2afe00f3d5e57f8519c9dd13834f`.
- Frozen runner/auditor/test hashes and remotely read-back freeze are recorded on #4733 before the formal invocation.

The parent #4258 result and all historical evidence remain unchanged. This successor quantifies a finite drift boundary; it does not establish a detector or recommend online adaptation.

