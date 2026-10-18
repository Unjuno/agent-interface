# A04 frozen run contract

- Allocation: `5309-WITNESS-A06-ORBSTACK-20261007` (fresh successor; A04/A05 STOPs are immutable)
- Issue: #5309; distinct successor to A03's immutable boundary result.
- Exact source base: `3dba6c86f212c37a2d80c844b816c38921a42cc5` (`origin/main` at freeze).
- Environment: OrbStack Docker 29.4.0, `orbstack` context, `linux/arm64`, Python 3.14.5 in a digest-pinned container; isolated `-I -S -B`; stdlib only.
- Container preflight: OrbStack Docker 29.4.0; fresh `docker info` and `docker ps` both exit 0. No running containers and no prior container with this allocation name. Initial image-store listing failed on an unrelated blob; pinned `python:3.14.5-slim` was then pulled successfully without deleting or modifying any existing container. Platform `linux/arm64`, RepoDigest `python@sha256:c845af9399020c7e562969a13689e929074a10fd057acd1b1fad06a2fb068e97`, image ID `sha256:c845af9399020c7e562969a13689e929074a10fd057acd1b1fad06a2fb068e97`.
- Candidate and auditor: one invocation each, no retries. Outputs use exclusive-create mode. Candidate is run first; auditor only if candidate exits zero and raw artifact exists.
- Frozen source hashes (SHA-256):
  - `fixture.json`: `ed0a03062de9cbe3c66352609458f0fe9bab31acded13c443c55014e9a970ac3`
  - `candidate.py`: `3294c98b9ce609ecb972bc110d488d363c1e6791182663c29756d2699203b5be`
  - `auditor.py`: `a3d1c23e0b369fca30abb4644c1947a286e29bc49a532ab22dcc7224c6981117`
  - `test_construction.py`: `d5bbb27cc8468b485856ce3cf6f31efb9cf1cb53838d20396a951267a41c3b88`

## H / T / D / C / U

- **H:** Given equal one-bit model-predicted information gain and the same admitted action set, a generic IG ranker deterministically selects the lexically first action. In the primary realized transition it emits an exact hidden-state receipt but destroys the only independent effect witness, so completion must remain UNKNOWN. A witness-aware ranker chooses the equal-cost action whose model predicts witness retention and obtains an independently verifiable completion.
- **T:** In pinned, network-disabled, read-only Linux/arm64 Python container with only the allocation directory mounted writable, exhaustively execute two hidden states × seven scenarios × four arms (56 rows). Both primary actions have equal task utility, cost, predicted IG, and admission. Controls cover pre-existing witness, no safe path, stale receipt, duplicate receipt identity (consume once), urgent stop/release, and model/receipt payload mismatch. Candidate sees model and receipt payload, never the truth table. Auditor independently reconstructs rank order, hidden-state effect, receipt freshness/type, witness survival, commits, and authority; it rejects six declared corruption classes.
- **D:** Scoped PASS only if the exact 56-row raw output matches the independently reconstructed decision for every row; primary GENERIC_IG is `UNKNOWN_EFFECT_WITNESS_LOST`; primary WITNESS_AWARE is `COMPLETE`; both arms expose identical admitted sets; no-path/stale/model mismatch remain UNKNOWN, duplicate identity is consumed once, urgent stop releases before commit, authority grants remain zero, and all frozen mutations are rejected by construction checks. Any discrepancy is retained as FAIL/HOLD/STOP without rerun.
- **C:** This finite authored fixture is intentionally favorable to a witness-aware tie-break. A mandatory postcondition readback, pre-existing witness, a better transition model, or forbidding task-action selection by generic IG may remove the difference.
- **U:** Synthetic state/receipt model only. No GUI, model, live input, user task, runtime, product benefit, natural frequency, or physical release claim. Host execution does not establish container isolation or performance.

## Exact execution commands

```sh
docker run --rm --platform linux/arm64 --name ai5309-witness-a06-candidate-20261007 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop ALL --security-opt no-new-privileges --pids-limit 32 --memory 256m --cpus 1 --user 501:20 --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/agent-interface-5309-witness-a04/research/analysis/dual_control_5309_witness_a06_20261007,dst=/work --workdir /work python@sha256:c845af9399020c7e562969a13689e929074a10fd057acd1b1fad06a2fb068e97 python -I -S -B candidate.py
docker run --rm --platform linux/arm64 --name ai5309-witness-a06-auditor-20261007 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop ALL --security-opt no-new-privileges --pids-limit 32 --memory 256m --cpus 1 --user 501:20 --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/agent-interface-5309-witness-a04/research/analysis/dual_control_5309_witness_a06_20261007,dst=/work --workdir /work python@sha256:c845af9399020c7e562969a13689e929074a10fd057acd1b1fad06a2fb068e97 python -I -S -B auditor.py
```

Formal execution is allowed only while remote `main` remains exactly the frozen base SHA and source hashes match. Construction tests must pass before freeze. A04/A05 are preserved STOPs and will not be rerun. A06 uses the corrected Docker bind-mount syntax; candidate and auditor each run once with no retries.
