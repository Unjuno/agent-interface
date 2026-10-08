# Run log — Issue #5550 successor 04B

- Coordination assignment: #5085 comment #5922184340; Issue preregistration:
  #5550 comment #5922258479.
- Allocation: `MAXPERM-SUPERVISOR-5550-T0-ORBSTACK-SUCCESSOR-20261001-04B`.
- Assigned window: `[2026-10-01T00:50:00Z, 2026-10-01T01:05:00Z)`.
- Start-gate host time: `2026-10-01T00:50:26Z`.
- Current main at gate: `7f78c6131a23c0a1a9f6c388ab26a567e5f7dfdf`.
- Source SHA-256: model `93ebe16ff1117c3c05a300f4e032a4391d3e9356adfa5b628b6560005ecd2e64`;
  auditor `7f4b974153b3ab2556f660fd9c4e7d361145f19ab3dc8cd20d7f575d2b305673`;
  tests `996f765adc354858449fd644be56fbc2c32fecabe7bf611ebc4b43d50a84f8bd`.
- Context/engine: `orbstack`, Docker Engine 29.4.0, `linux/aarch64`.
- Cached image verification: exact RepoDigest matched
  `python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
  platform `linux/arm64`; no pull/build.
- Initial container inventory: empty. Guard status: `PASS_PRELAUNCH_GATE`.

## Candidate invocation

```sh
docker --context orbstack run --rm --platform linux/arm64 --network none \
  --read-only --cap-drop ALL --security-opt no-new-privileges \
  --cpus 1 --memory 536870912 --pids-limit 64 \
  -v "$PWD/research/analysis/max_permissive_supervisor_5550_t0_20261001:/work:ro" \
  --entrypoint python3 \
  python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  -B /work/model.py
```

- Exit: 0; stdout 23,906 bytes; stderr 0 bytes.
- `formal-01.json` SHA-256:
  `f17273be18b33083353a883c47c2834a3c33457cb4daada2227aeaf00bd6eb8b`.
- Exact match to predecessor raw; parsed row count 108.

## Separate raw-only auditor invocation

```sh
docker --context orbstack run --rm --platform linux/arm64 --network none \
  --read-only --cap-drop ALL --security-opt no-new-privileges \
  --cpus 1 --memory 268435456 --pids-limit 64 \
  -v "$PWD/research/analysis/max_permissive_supervisor_5550_t0_20261001/audit.py:/audit.py:ro" \
  -v "$PWD/research/analysis/max_permissive_supervisor_5550_successor04_20261001/raw/formal-01.json:/raw/formal-01.json:ro" \
  --entrypoint python3 \
  python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  -B /audit.py /raw/formal-01.json
```

- Exit: 0; stdout 199 bytes; stderr 0 bytes.
- `audit-01.json` SHA-256:
  `594e785a1a607c7bdab636e3687201fc225d0e0075ca0eec1be6423db60aad2d`.
- Exact match to predecessor audit; audit errors empty, 44 safe/nonblocking
  supervisors found by exhaustive enumeration.

## Post-run checks

- Host time after both containers: `2026-10-01T00:51:57Z`.
- `docker --context orbstack ps --quiet`: empty.
- Targeted local tests: model 7/7; prelaunch guard 14/14.
- Analysis-index CI initially failed because this new retained result directory
  was absent from `research/analysis/README.md`; generated index refreshed
  locally to 254 entries and `python research/analysis/check_index.py` passed.
- No retry; no other container started by this allocation. Formal lane released.
