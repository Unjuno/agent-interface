# T7 start gate and execution record

- Allocation: `SEMANTIC-RECEIPT-5442-T7-WSLC-20261002-01`
- Frozen branch: `research/semantic-receipt-5442-t7-wslc-20261002`
- Source branch base: `900c48368909a247ffd2b1b4dddd944cd6008d90`.
- Immediately before execution, main was `8150aa7f55c490bc1f1cdd861c764ec27d2e3fb2`, one commit ahead of the freeze. The compare showed that intervening commit changed only `docs/IDEAS_AND_OUTCOMES.md` and `docs/RESEARCH_ISSUE_INDEX.md`; it did not touch this package or its source dependencies. Frozen files on the experiment branch matched the local bytes exactly before candidate launch.
- WSLc client/server: 3.0.1.0. Pre-run container inventory had only the previously stopped `ai-wsl301-migration-smoke-01`; it was not touched. Python image was already cached, Linux/amd64, repo digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`.
- Formal output directory `formal_01/` was absent before the freeze and before launch.
- Candidate source and scenario mounts were inspected read-only. Candidate container was network `none`, one CPU, configured memory 1 GiB, user `65534:65534`, workdir `/src`; command exited 0 at `2026-10-02T04:39:09.778233286Z`. Container ID `b2ae1425552a8924621226b6417a3a886fac3a8a030046e7d035b7507c2bdad0`.
- After validating one complete four-row raw JSON, auditor ran once in a distinct container. Source and raw mounts were both inspected read-only. Auditor container was network `none`, one CPU, configured memory 1 GiB, user `65534:65534`, workdir `/src`; command exited 0 at `2026-10-02T04:39:52.685569769Z`. Container ID `5722b381f89228af89bba5d5e567ccdf78fc2e1d268b81b9e950b0f6cd973647`.
- Both invocations emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Therefore the configured 1 GiB is not claimed as enforced; memory enforcement was not an outcome gate.
- Candidate=1, auditor=1, retries=0. Both containers are retained stopped; no existing container/image was removed or altered.
