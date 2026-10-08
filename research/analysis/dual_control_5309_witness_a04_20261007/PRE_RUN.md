# A04 frozen run contract

- Allocation: `5309-WITNESS-A04-HOSTCPU-20261007`
- Issue: #5309; distinct successor to A03's immutable boundary result.
- Exact source base: `9f49b75e72e4dc0596dbfcf2bc7beb7af72652ec` (`origin/main` at freeze).
- Environment: macOS 27.0.1 arm64, Python 3.14.5, isolated `-I -S -B`; stdlib only.
- Container preflight: OrbStack 2.1.3 / Docker 29.4.0, context `orbstack`; `docker info` succeeded but `docker ps` failed to enumerate containers with `blob sha256:08e8b41ebd1476eff067939e0192d49e4014c21bab11a4d793429187e4242704 returned operation not supported`. STOP container execution; no container isolation claim. This host fallback is explicitly allowed by the Issue preregistration.
- Candidate and auditor: one invocation each, no retries. Outputs use exclusive-create mode. Candidate is run first; auditor only if candidate exits zero and raw artifact exists.
- Frozen source hashes (SHA-256):
  - `fixture.json`: `ae0deb71736e25f59b84d07591a9e357632a8420f57aa95a9f80d62979095fa9`
  - `candidate.py`: `3294c98b9ce609ecb972bc110d488d363c1e6791182663c29756d2699203b5be`
  - `auditor.py`: `a3d1c23e0b369fca30abb4644c1947a286e29bc49a532ab22dcc7224c6981117`
  - `test_construction.py`: `d5bbb27cc8468b485856ce3cf6f31efb9cf1cb53838d20396a951267a41c3b88`

## H / T / D / C / U

- **H:** Given equal one-bit model-predicted information gain and the same admitted action set, a generic IG ranker deterministically selects the lexically first action. In the primary realized transition it emits an exact hidden-state receipt but destroys the only independent effect witness, so completion must remain UNKNOWN. A witness-aware ranker chooses the equal-cost action whose model predicts witness retention and obtains an independently verifiable completion.
- **T:** Exhaustively execute two hidden states × seven scenarios × four arms (56 rows). Both primary actions have equal task utility, cost, predicted IG, and admission. Controls cover pre-existing witness, no safe path, stale receipt, duplicate receipt identity (consume once), urgent stop/release, and model/receipt payload mismatch. Candidate sees model and receipt payload, never the truth table. Auditor independently reconstructs rank order, hidden-state effect, receipt freshness/type, witness survival, commits, and authority; it rejects six declared corruption classes.
- **D:** Scoped PASS only if the exact 56-row raw output matches the independently reconstructed decision for every row; primary GENERIC_IG is `UNKNOWN_EFFECT_WITNESS_LOST`; primary WITNESS_AWARE is `COMPLETE`; both arms expose identical admitted sets; no-path/stale/model mismatch remain UNKNOWN, duplicate identity is consumed once, urgent stop releases before commit, authority grants remain zero, and all frozen mutations are rejected by construction checks. Any discrepancy is retained as FAIL/HOLD/STOP without rerun.
- **C:** This finite authored fixture is intentionally favorable to a witness-aware tie-break. A mandatory postcondition readback, pre-existing witness, a better transition model, or forbidding task-action selection by generic IG may remove the difference.
- **U:** Synthetic state/receipt model only. No GUI, model, live input, user task, runtime, product benefit, natural frequency, or physical release claim. Host execution does not establish container isolation or performance.

## Exact execution commands

```sh
python3 -I -S -B research/analysis/dual_control_5309_witness_a04_20261007/candidate.py
python3 -I -S -B research/analysis/dual_control_5309_witness_a04_20261007/auditor.py
```

Formal execution is allowed only while remote `main` remains exactly the frozen base SHA. Construction tests have passed before freeze: 5 tests, zero failures. The first container preflight failure is retained; no container retry is authorized by this allocation.
