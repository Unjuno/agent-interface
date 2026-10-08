# Issue #2476 — r4 construction result

Allocation: `issue2476-track-cumulative-drift-evidence-construction-r4-20260928`  
Branch: `research/doom/track-drift-2476-r4-20260928`  
Frozen source commit: `ae175bcd8231d2d6f6a06591556c8b067d012626`  
Base main: `f3dc0f18b0aaef241a6cd34124b68439c3434b05`

## Disposition

- Technical construction result: `PASS_CUMULATIVE_DRIFT_EVIDENCE_CONSTRUCTION_ONLY`.
- Allocation/provenance disposition: `HOLD_PREREG_OUTPUT_PATH_IDENTITY`.

The local runner and separate auditor completed once each in Docker. All 60 scheduled rows reconciled, the technical gates passed, and no physical input was emitted. However, before execution `FREEZE.json` recorded the runner and auditor output mounts only as `<empty-run-output>` and `<empty-audit-output>`; it did not pin their absolute host paths. The actual directories were `C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-2\work\issue2476-r4-local\run-output` and `...\audit-output`. They were checked empty immediately before use, but that does not repair the missing preregistered path identities. Preserve the technical result, but do not promote r4 as a fully provenance-passing allocation. This is not a scientific failure and says nothing against H.

This r4 result is a distinct successor to r3's immutable `STOP_OPERATOR_INVOCATION_ERROR_NO_RETRY`; r3 was not rerun, repaired or relabelled. No formal #2476 visual matcher/task trajectory was invoked.

## Executed checks and commands

Docker image: `python:3.13.5-slim-bookworm`, ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`, linux/amd64; Docker Engine 29.8.0 linux/amd64. Both runs used `--pull=never --network=none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cpus=1 --memory=268435456 --memory-swap=268435456 --pids-limit=32 --cap-drop=ALL --security-opt=no-new-privileges`. The source mount was read-only. Runner/auditor outputs used separate host directories; the raw directory was read-only for audit. GitHub Actions/workflows were not used.

1. Frozen auditor unit suite: `python -B -m unittest -v test_audit.py` — 4/4 passed in Docker; exit 0. Retained at `logs/unit-tests.txt`.
2. Non-writing CLI preflight: `python -B /source/run.py --help` — exit 0 and confirmed required `--source SOURCE` and `--out OUT`; retained at `logs/runner-help.txt`.
3. Sole runner invocation:

```text
docker run --rm --pull=never --platform linux/amd64 --network=none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cpus=1 --memory=268435456 --memory-swap=268435456 --pids-limit=32 --cap-drop=ALL --security-opt=no-new-privileges --mount type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-2\work\issue2476-r4-local,target=/source,readonly --mount type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-2\work\issue2476-r4-local\run-output,target=/out --workdir=/source --entrypoint=python python:3.13.5-slim-bookworm -B /source/run.py --source /source --out /out
```

Exit 0; 20 policy-runs / 60 scheduled rows; `physical_input_emissions=0`. Raw SHA-256: `ce07a0b30aa504e929ac91372b38d0eb1281746e256ef35e9de02d3e8fcaed82` (23,438 bytes). stdout and exit receipt are under `logs/`.

4. Sole independent auditor invocation, in a separate Docker container:

```text
docker run --rm --pull=never --platform linux/amd64 --network=none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cpus=1 --memory=268435456 --memory-swap=268435456 --pids-limit=32 --cap-drop=ALL --security-opt=no-new-privileges --mount type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-2\work\issue2476-r4-local,target=/source,readonly --mount type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-2\work\issue2476-r4-local\run-output,target=/runout,readonly --mount type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-2\work\issue2476-r4-local\audit-output,target=/auditout --workdir=/source --entrypoint=python python:3.13.5-slim-bookworm -B /source/audit.py --source /source --raw /runout/raw.json --out /auditout
```

Exit 0; `errors=[]`; 20 runs / 60 scheduled rows; raw hash and case hash matched; 4/4 corruption controls rejected: missing suffix emission flag, true suffix emission flag, missing scheduled row, reordered runs. Audit SHA-256: `3855536df96cf3a4df5ad3282d382452654bbf7835d72b8c0fc2a222431aa0dd` (596 bytes).

## Technical observations

| Frozen case | Per-hop-only | Per-hop + 12 px global cap |
|---|---|---|
| Exact, three hops | TRACKED 3/3 | TRACKED 3/3 |
| Cumulative drift exactly 12 px | TRACKED 3/3 | TRACKED 3/3 |
| Repeated 8 px residual; exceeds cap at hop 2 | TRACKED 3/3 | TRACKED, ABSTAIN at hop 2; suffix explicitly `NOT_REACHED_AFTER_STOP` |
| Cumulative drift crosses 12 px at hop 3 | TRACKED 3/3 | TRACKED, TRACKED, ABSTAIN at hop 3 |
| Abrupt translation / target disappearance | ABSTAIN at hop 2 | ABSTAIN at hop 2 |
| Score below gate | ABSTAIN at hop 3 | ABSTAIN at hop 3 |
| Stale hop age / frame sequence gap | ABSTAIN at hop 2 | ABSTAIN at hop 2 |
| Geometry change | ABSTAIN at hop 3 | ABSTAIN at hop 3 |

All 60 reached or skipped rows contain the JSON boolean `physical_input_emitted: false`. These are synthetic construction observations only, not real target tracking or task-control evidence.

## Source integrity and scope

The five source SHA-256 values remained byte-identical to the pre-execution freeze and GitHub-readback blobs: PLAN `96297473f49568f18e1677437018df0309c15d93c58efc90325fa01346ab1994`; cases `7a8de796075fe31b1134bc5bd44c0202d77adaaeaf147be39cdeb357567520d2`; runner `e34b4a0809f68ed60e2d26e41f4f24eab3f570b196c7a7968db26cf598168ac8`; auditor `bed497c4be729b30b67e1f256eb93d6d7c252c3cd8ec971f69c9cafb005aa907`; tests `d13656794d7eeb57466444902fde1431c300426d6a9630756ee01ddcc0ca44ab`.

No new source tuning, rerun, replacement, formal matcher call, GUI/game/model/provider call, or physical input occurred. This result does not establish real visual tracking, task effect, release safety, 12 px optimality, or formal #2476 BASELINE/TRACKED/ABSTAIN benefit. The r4 path-identity HOLD is retained as-is; any future successor must freeze exact host output paths before execution and must not reuse r4's allocation ID or relabel its provenance disposition.
