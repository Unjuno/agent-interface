# Formal allocation 03 — execution record

- Allocation: `INFRA-SPEED-FAIRNESS-6347-T0-20261002-03`.
- Preregistration: Issue #6347 comment `5943233639`.
- Frozen source base: `c69fa71501a0e42abc3ffe435ae72949d5d15877`.
- Candidate invocations: 1; independent auditor invocations: 1; retries: 0.
- Engine: OrbStack Docker Engine 29.4.0, Linux/aarch64, cgroup v2.
- Image ID: `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`python:3.12-slim`, linux/arm64).
- Isolation: `--network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop ALL --security-opt no-new-privileges`; all source/raw inputs mounted read-only. Memory is configured, not claimed as host-enforced.

## Candidate command

```sh
docker run --rm --pull never --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/infra_speed_fairness_6347_boundary_successor_v1/candidate.py,dst=/src/candidate.py,readonly \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/infra_speed_fairness_6347_boundary_successor_v1/fixture.json,dst=/src/fixture.json,readonly \
  --tmpfs /tmp:rw,noexec,nosuid,size=8m \
  sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python /src/candidate.py /src/fixture.json
```

stdout bytes are `candidate.raw.json`; stderr is `candidate.stderr.txt`; process status is `candidate.exit`.

## Independent raw-only auditor command

```sh
docker run --rm --pull never --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/infra_speed_fairness_6347_boundary_successor_v1/audit.py,dst=/src/audit.py,readonly \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/infra_speed_fairness_6347_boundary_successor_v1/fixture.json,dst=/src/fixture.json,readonly \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/infra_speed_fairness_6347_boundary_successor_v1/results/formal-03/candidate.raw.json,dst=/src/candidate.raw.json,readonly \
  --tmpfs /tmp:rw,noexec,nosuid,size=8m \
  sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python /src/audit.py /src/fixture.json /src/candidate.raw.json
```

stdout bytes are `audit.raw.json`; stderr is `auditor.stderr.txt`; process status is `auditor.exit`. The auditor did not receive candidate source.

## Captured outcome

- Candidate exit 0; 16 raw rows; stderr empty.
- Auditor exit 0; exact 16/16 reconstruction; all four frozen mutations rejected; stderr empty.
- Phase and strategic-send paired boundaries each change from A+B collected / B wins at ready tick 4 to only A collected / A wins at tick 6.
- All exact file hashes are in the parent `SHA256SUMS`.
