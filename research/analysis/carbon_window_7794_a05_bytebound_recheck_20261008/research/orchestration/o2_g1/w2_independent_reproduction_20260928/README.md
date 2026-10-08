# O2 G1 W2 independent reproduction (2026-09-28)

This additive record independently reproduces the source-only synthetic measurement-contract result on current `main`. It does not modify the original W2 artifacts or expand their claim to live input, gameplay, task efficacy, or recovery efficacy.

- Main source commit: `2b4891d99e3b938d1595d75ec978eb2e4ce6f5bf`
- Run record: `research/orchestration/o2_g1/w2_measurement_v2_20260927/RUN_RECORD.json`
- Runtime: Docker Desktop `desktop-linux`, Engine `28.5.1`; network disabled, source read-only, root filesystem read-only, 1 CPU, 512 MiB, 32 pids.
- Frozen record requested `python:3.12-slim-bookworm` with digest `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`. The tag was not cached, so no pull was attempted. Local `python:3.12-slim` resolved to that exact image digest and was used.
- Command: `sh /src/run_validation.sh`
- Result: verifier PASS 8/8; independent raw audit PASS; 5 numeric reconstructions; 7/7 corruption controls rejected; 0 mismatches. Overlap union 58 ns vs naive sum 76 ns.
- All five code/input SHA-256 values and both generated output SHA-256 values are recorded in `REPRODUCTION.json`.
- Limits: these are synthetic source-contract cases only. The runner checks only schema fields/refs it uses; no external JSON Schema meta-validator was run. No live/game/model/input effect or recovery efficacy is established.
- Initial failed invocation is preserved in `REPRODUCTION.json`: the requested historical image tag was absent locally. No network was enabled and no test code ran during that attempt.

Reproduce from this directory with Docker Desktop and the recorded image digest using `sh run_validation.sh` under equivalent read-only/network-disabled mounts. `VERIFICATION.json` and `AUDIT.json` are frozen results from the independent local run.

