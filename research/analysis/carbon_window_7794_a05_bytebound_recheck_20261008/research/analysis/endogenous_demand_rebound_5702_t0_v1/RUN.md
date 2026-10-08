# T0 execution record

- Issue: #5702; frozen H/T/D/C/U and source identities: [FREEZE.md](FREEZE.md).
- Execution date: 2026-10-01 UTC; source commit `a3abff7075a819dc04da57d63591372f263c6698`; main parent `0764c928f1a32a3c7f992f1b80cb62f774e2d7ed`.
- Host: macOS 26.6.2, Darwin 25.6.0, Apple arm64.
- Runtime: CPython 3.12.13 at `/run/current-system/sw/bin/python3.12`; standard library only.
- Route: host-only. The T0 explicitly requested no container/GPU allocation; the available tool inventory has no Obstac integration. No Docker/OrbStack, model, GUI, runtime, network call, input or external effect was used. This is not containerized evidence.
- Formal candidate: one CLI invocation, exit 0; produced 22 raw opportunity rows in `candidate.json`; stderr empty. Raw SHA-256 `f4187c88ecf459202b208ed71bdb065dbbe5d00cd98c47770674704150ae0b37`.
- Independent audit: one separate raw-only CLI process, exit 0; `PASS`, zero errors, 8/8 corruption controls rejected. Audit JSON SHA-256 `11e0227697fd10d0466dfb5f56ee3b3d47f8d2e30486142ccc7864f71fd91e72`; stderr empty.

Exact commands, from repository root:

```text
python3.12 -B research/analysis/endogenous_demand_rebound_5702_t0_v1/candidate.py > research/analysis/endogenous_demand_rebound_5702_t0_v1/results/formal-host-01/candidate.json 2> research/analysis/endogenous_demand_rebound_5702_t0_v1/results/formal-host-01/candidate.stderr
python3.12 -B research/analysis/endogenous_demand_rebound_5702_t0_v1/audit.py research/analysis/endogenous_demand_rebound_5702_t0_v1/results/formal-host-01/candidate.json > research/analysis/endogenous_demand_rebound_5702_t0_v1/results/formal-host-01/audit.json 2> research/analysis/endogenous_demand_rebound_5702_t0_v1/results/formal-host-01/audit.stderr
```

Both processes used only the frozen standard-library source. The preflight unittest suite was 8/8 before the formal candidate; it is source validation and not an additional formal sample. Formal candidate and auditor counts are exactly one each; retries=0.
