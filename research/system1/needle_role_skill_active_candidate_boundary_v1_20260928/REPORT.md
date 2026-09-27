# Issue #4986 Stage 0 — candidate publication construction contract

## H / T / D / C / U

**H.** A versioned inert role-skill candidate can be validated before publication: only exact package/schema/generation/scope plus an audit receipt may replace ACTIVE; invalid or unknown validation leaves prior ACTIVE bytes untouched; proposals bound to a retired generation yield; rollback restores a retained package only while compatible.

**T.** Allocation `needle-role-skill-active-candidate-boundary-v1-stage0-20260928-01`, Issue #4986. Base main `b7816b25b452f8411c2690a69297578bdc4c378a`. Branch `research/needle-role-skill-active-candidate-boundary-v1-20260928`; additive path `research/system1/needle_role_skill_active_candidate_boundary_v1_20260928/`. The input is the exact inert `skill.json` Git blob `45b80150dac503f4eb6f3cb5d82f9afa2c587107` from #3890 seed 3788 (SHA-256 `2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a`, 15,279 bytes). The synthetic construction runner and separate raw-only auditor were each run once in separate network-disabled containers using cached `python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` (linux/amd64, Docker Engine 28.5.1, 1 CPU, 512 MiB, 64 PIDs, read-only root and source). Nine cases were retained: valid publish; tamper; missing receipt; stale intent; stale schema; unknown validator; stale proposal; compatible rollback; incompatible rollback.

**D.** Raw-only audit reconstructed 9/9 cases with zero errors: `PASS_CONSTRUCTION_CONTRACT_SCOPED`. Six independent corruption controls (decision, candidate bytes, before digest, rollback digest, stale dispatch count, missing event) were rejected 6/6. Valid candidate advanced generation 3788→3789 after receipt binding; all rejection/yield cases retained ACTIVE digest and byte length; the stale proposal had zero dispatch; compatible rollback restored the exact original bytes; incompatible rollback was rejected. Raw SHA-256 `84c39bfa134d6b788423378faedb763524f409de4eedfa09ca8c983859663250` (167,611 bytes); audit SHA-256 `ada26163593e23a5a09ce3aaedc542521c56931034b48e170240a02d16d1bf41`.

**C.** One hand-authored finite lifecycle model, one reused synthetic package, and no concurrent readers/writers. The model has no filesystem/process crash or memory-ordering test. SHA-256 is an integrity identifier, not a signature. Stage 0 is construction evidence, not the separately registered Stage 1 concurrency probe.

**U.** No claim about adapted Needle competence, Astra corrections, natural-language routing, real task effects, execution authority, hostile package security, concurrent runtime publication, performance, production safety, or product readiness. No consumed training allocation was reused and no model fitting occurred.

## Exact commands

Runner:

```powershell
docker run --pull=never --rm --network=none --read-only --cpus=1 --memory=512m --pids-limit=64 --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,source=<stage0-dir>,target=/src,readonly" --mount "type=bind,source=<stage0-dir>\raw,target=/evidence" --workdir /src python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 python -B runner.py
```

Independent auditor (distinct invocation):

```powershell
docker run --pull=never --rm --network=none --read-only --cpus=1 --memory=512m --pids-limit=64 --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,source=<stage0-dir>,target=/src,readonly" --mount "type=bind,source=<stage0-dir>\raw,target=/raw,readonly" --mount "type=bind,source=<stage0-dir>\audit,target=/audit" --workdir /src python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 python -B audit.py
```

## Evidence map

- `FREEZE.json`: source, image, allocation, gates, outcome hashes and limits.
- `skill.json`, `runner.py`, `audit.py`: exact mounted inputs.
- `test_controls.py`: six corruption controls against the raw-only auditor.
- `raw/raw.json`: all nine ordered transitions, candidate bytes, before/after ACTIVE digests and decisions.
- `audit/audit.json`: independently reconstructed decision and integrity result.

Next scientific discriminator under #4986 is the separately frozen, bounded Stage 1 reader/writer boundary probe. It must not be inferred from this Stage-0 pass.

