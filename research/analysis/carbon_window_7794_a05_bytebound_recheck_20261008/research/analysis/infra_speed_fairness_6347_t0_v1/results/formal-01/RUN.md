# Formal allocation 01 — execution record

- Allocation: `INFRA-SPEED-FAIRNESS-6347-T0-20261002-01`
- Preregistration: Issue #6347 comment `5943061737`.
- Frozen source base: `f70aa50832ffa84c325237f5367c02332335a156`.
- Candidate invocations: 1; independent auditor invocations: 1; retries: 0.
- Engine: OrbStack, Docker 29.4.0, Linux/aarch64, cgroup v2.
- Image ID: `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`python:3.12-slim`, linux/arm64).
- Isolation: `--network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop ALL --security-opt no-new-privileges`; source and fixture mounts read-only. The raw artifacts were redirected to the host output directory. The configured memory limit is not promoted to a hard-enforcement claim.

## Candidate command

```sh
docker run --rm --pull never --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/infra_speed_fairness_6347_t0_v1/candidate.py,dst=/src/candidate.py,readonly \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/infra_speed_fairness_6347_t0_v1/fixture.json,dst=/src/fixture.json,readonly \
  --tmpfs /tmp:rw,noexec,nosuid,size=8m \
  sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python /src/candidate.py /src/fixture.json
```

stdout bytes are `candidate.raw.json`; stderr is `candidate.stderr.txt`; process status is `candidate.exit`.

## Independent auditor command

```sh
docker run --rm --pull never --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/infra_speed_fairness_6347_t0_v1/audit.py,dst=/src/audit.py,readonly \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/infra_speed_fairness_6347_t0_v1/fixture.json,dst=/src/fixture.json,readonly \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/infra_speed_fairness_6347_t0_v1/results/formal-01/candidate.raw.json,dst=/src/candidate.raw.json,readonly \
  --tmpfs /tmp:rw,noexec,nosuid,size=8m \
  sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python /src/audit.py /src/fixture.json /src/candidate.raw.json
```

stdout bytes are `audit.raw.json`; stderr is `auditor.stderr.txt`; process status is `auditor.exit`. Auditor container received no candidate source.

## Captured outcome

- Candidate: exit 0; stdout retained as 129-row `candidate.raw.json`; stderr empty.
- Auditor: exit 0; `pass=true`, 129/129 exact row reconstruction, four of four mutation controls rejected; stderr empty.
- Independent sensitivity: FRFS 14/14 pairs changed; arrival FIFO 0/14; batch rotate 0/14.
- All exact file hashes are in the parent `SHA256SUMS`.
