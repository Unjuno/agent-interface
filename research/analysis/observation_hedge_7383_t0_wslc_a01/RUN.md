# Issue #7383 T0 allocation 01 — first outcome

## Disposition

`PASS_METHOD_SCOPED`; the frozen numeric hypothesis `H_PASS_SCOPED` holds only for the authored heavy-tail stratum. No live-observation or task-benefit claim follows. Candidate exit 0, independent auditor exit 0, retries 0. The four frozen corruption controls were rejected; the auditor reconstructed 600/600 arm rows with `errors=[]`.

## Execution record

- Observed complete at 2026-10-04T02:47:53Z (the time this post-run checksum/state inspection completed; exact per-process start/finish timestamps were not collected).
- Main immediately before execution remained `13bab54ea6d91978247ecc1b70e5060db752367a`; no intervening main change was observed from intake.
- Candidate command: `wslc run --rm --name ai-7383-t0-a01-candidate --pull never --network none --cpus 1 --memory 512M --volume "C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-github-mcp-main-2\work\7383-observation-hedge-t0-wslc-a01:/src:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-github-mcp-main-2\work\7383-observation-hedge-t0-wslc-a01\out:/out:rw" --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B candidate.py`.
- Candidate stdout: `{"status": "CANDIDATE_COMPLETE", "threshold": 11, "cases": 200, "rows": 600}`. Exit 0.
- Auditor command: `wslc run --rm --name ai-7383-t0-a01-auditor --pull never --network none --cpus 1 --memory 512M --volume "C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-github-mcp-main-2\work\7383-observation-hedge-t0-wslc-a01:/src:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-github-mcp-main-2\work\7383-observation-hedge-t0-wslc-a01\out:/out:rw" --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B audit.py`.
- Auditor stdout is summarized in `out/audit.json`: 600 rows, threshold 11 ms, no errors, four of four controls rejected, `PASS_METHOD_SCOPED`. Exit 0.
- Both WSLc invocations emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The requested 512 MiB limit was accepted, but effective memory/swap enforcement is unknown.
- Immediate post-run `wslc container list` showed no running containers. No unrelated image/container was modified or deleted.

## Results (all strata, n=40 per arm)

| Stratum | Single p95 / mean work | Delayed p95 / mean work | Delayed valid | Interpretation |
|---|---:|---:|---:|---|
| heavy_tail | 80 ms / 13.30 | 14 ms / 7.20 | 40/40 | 82.5% p95 reduction; mean work ratio 0.541; meets the frozen numeric H gates |
| correlated | 16 ms / 11.75 | 16 ms / 13.25 | 40/40 | No p95 gain; 12.8% more mean work |
| shared_queue | 12 ms / 8.50 | 20 ms / 10.625 | 40/40 | p95 worsens 66.7%; 25% more mean work |
| cancel_lag | 30 ms / 23.85 | 18 ms / 28.175 | 40/40 | 40% lower p95 but 18.1% more mean work; cancellation tail matters |
| generation_flip | INF / 8.50 | INF / 9.125 | 5/40 | Freshness gate prevented stale admission; delayed secondary yielded a current result in 5 cases but p95 remained unavailable because >5% cases had no valid observation |

The immediate-duplication diagnostic p95/work by stratum is available in the raw auditor summary: heavy-tail 6 ms / 8.35; correlated 16 ms / 23.50; shared-queue 14 ms / 19.45; cancel-lag 7 ms / 21.675; generation-flip INF / 13.50. This diagnostic has higher or comparable work and is not the adopted policy.

`INF` means fewer than the nearest-rank 95th-percentile number of cases produced an admissible complete-current observation; unavailable rows remain in the denominator.

## Integrity and hashes

- Candidate source SHA-256: `dd0cdea25f5706a30e4844a376502e0f5f59a0b5938aeb0dddafe1d9a4a7062`.
- Independent auditor source SHA-256: `ba03088faa733490d9567915c35d6bbf10d8cf4a1ba4c2768210d84af5af02eb`.
- Freeze SHA-256: `6be5534b1c9576f454e1f30802ac059aeab96f1da3f34e98ffc8537ec3207642`.
- Candidate raw SHA-256: `8b8479edb15f8b7183abdd46767ddf2ba1b9da8199f5308759b6edfeac7de9ab` (168,136 bytes).
- Transport copy `candidate.json.gz` SHA-256: `2be623a95c52a2bd02f1f3fa39e643bfd13ebc2637cd6870cac30b439e356e8b` (5,050 bytes); decompression independently reproduced all 168,136 raw bytes and the raw SHA-256 above.
- GitHub retains that transport copy as `formal_01/candidate.json.gz.b64`; base64-decode, then gzip-decompress to recover the byte-exact candidate JSON.
- Auditor JSON SHA-256: `f5f23be7d4551ab30ee3357b61c3f249860af643b6b26212df19ae2bf4846382` (3,194 bytes).
- The auditor is a separate implementation and does not import the candidate. It reconstructed all expected rows from its own enumeration, then rejected partial response, stale-generation-first, double-admission and omitted-loser-work mutations. These are finite checks of this fixture only.

## Scope and next question

This is a deterministic synthetic construction, not measured request service-time data. The favorable case is intentionally heavy-tailed and cancellation is immediate there; the shared-queue and cancellation-lag strata demonstrate that the effect can reverse or cost more. The generation-flip cases also show that “first completion” cannot override currentness. No real X11/Xvfb acquisition, compositor interference, task effect/deadline, model, user desktop, actuation, human tempo, end-to-end latency, GPU, or memory-limit enforcement was tested. No runtime adoption is authorized by this result.

Before any T1, first verify an actual eligible observation straggler on the critical path and obtain a separate allocation/ownership check; the issue's private Xvfb step remains unrun. Preserve this first outcome unchanged.
