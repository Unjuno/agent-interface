# RUN_LOG — #5550 T0

## Frozen pre-run state

- Main: `716f8864948023abb3f70f60a5053c66ec4c2737`.
- Preregistration branch commit: `d73031fb3790b43b1b6afdf96c68b05e2eaf4353`.
- Allocation: `MAXPERM-SUPERVISOR-5550-T0-ORBSTACK-20260930-02`.
- Candidate hash: `93ebe16ff1117c3c05a300f4e032a4391d3e9356adfa5b628b6560005ecd2e64`.
- Auditor hash: `7f4b974153b3ab2556f660fd9c4e7d361145f19ab3dc8cd20d7f575d2b305673`.
- Tests hash: `996f765adc354858449fd644be56fbc2c32fecabe7bf611ebc4b43d50a84f8bd`.
- Local tests: 7/7; compile, freeze JSON parse, index and diff checks passed.
- Immediate pre-run fetch confirmed main still at the frozen SHA. OrbStack image inspection confirmed exact digest and `linux/arm64`; image Config.Cmd was `python3`, no Entrypoint key. Immediate pre-run `docker ps` returned no running containers.

## Formal commands and outcomes

Candidate — exactly one invocation, exit 0:

```sh
docker --context orbstack run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --cpus 1 --memory 536870912 --pids-limit 64 --tmpfs /tmp:rw,nosuid,noexec,size=16m -v "$PWD:/work:ro" --entrypoint python3 sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 -B /work/model.py > raw/formal-01.json
```

Candidate stdout is `raw/formal-01.json`; SHA-256 `f17273be18b33083353a883c47c2834a3c33457cb4daada2227aeaf00bd6eb8b`; 108 transition rows. JSON parse succeeded.

Independent auditor — separate container, exactly one invocation after candidate exit 0, exit 0:

```sh
docker --context orbstack run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --cpus 1 --memory 268435456 --pids-limit 64 --tmpfs /tmp:rw,nosuid,noexec,size=16m -v "$PWD:/work:ro" --entrypoint python3 sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 -B /work/audit.py /work/raw/formal-01.json > raw/audit-01.json
```

Audit stdout is `raw/audit-01.json`; SHA-256 `594e785a1a607c7bdab636e3687201fc225d0e0075ca0eec1be6423db60aad2d`; status `PASS_T0_SYNTHETIC_SCOPE`; errors empty. Auditor received only its own code plus candidate raw through the read-only fixture mount; it did not import `model.py`.

## Closeout

After both containers exited, a read-only `docker ps` listed running containers named `concentration-aware-ns:checker` and `cans-cusp-spatial-compile`. They were not inspected, stopped, or otherwise touched. No further container invocation was made under this allocation.
