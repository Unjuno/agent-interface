# Online role-router LoRA skills — Needle/System 1 experiment

Research-only successor to Issues #3912, #4888 and #4895. This experiment tests a role-network boundary plus isolated, versioned skills, not natural-language role inference or production learning.

## Design

Four paired arms receive identical A-base weights, B support arrival order, LoRA initialization and update budget (16 arrivals × 8 optimizer updates = 128): `SHARED_B_ONLY`, `SHARED_A_REPLAY` (one B row plus one cyclic A-memory row per update), `ROUTED_SHARED_ADAPTER` (role/scope/generation receipt but shared parameters), and `ROUTED_SEPARATE_SKILLS` (role A maps to immutable A skill; role B maps to its separate online rank-2 LoRA skill). Unknown roles, stale generations and wrong scopes yield with no adapter proposal. The independent auditor reconstructs every arm separately and intentionally does not require bit-exact state equality between distinct batch shapes.

Formal allocation: seeds 736211, 736311, 736411. Excluded full-pipeline construction seed: 736014. Hypothesis, thresholds and scope are preregistered in #4899 before any formal fitting. Formal success requires every seed to pass the independent raw/source audit, frozen A skill and base, fail-closed route controls, all updates <60ms, routed separate-skill held-out A/B >=0.90, A >=0.10 above each shared online arm, and B within 0.10 of the best shared online B.

## Docker protocol

Use only the cached Linux/amd64 image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, `--pull=never`, `--network=none`, readonly source/root, 1 CPU, 2 GiB, 64 PIDs and a 64 MiB tmpfs. Construction suite performs zero optimizer updates:

```powershell
docker run --rm --pull=never --network=none --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt=no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=64m --mount "type=bind,source=<source-dir>,dst=/src,readonly" --workdir /src -e PYTHONDONTWRITEBYTECODE=1 sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e -m unittest -v test_construction
```

Run `construction.ps1` only into a new empty output directory; independently audit its raw using `construction_audit.ps1` and another empty report directory. It is not formal evidence. Confirm no concurrent Docker experiment shares the CPU before the one `formal.ps1` orchestration. Then run `audit.ps1` once into a distinct empty directory. All wrappers retain exact stdout/stderr and argv/exit/byte/hash receipts; no retries or tuning. `FREEZE.sha256` is exactly 64 lowercase hex plus LF.

No runtime/product code is changed. A synthetic role bit, small CPU model, three seeds and isolated experiment do not establish real agent utility, natural-language router quality, end-to-end latency, safety/action authority or production readiness.
