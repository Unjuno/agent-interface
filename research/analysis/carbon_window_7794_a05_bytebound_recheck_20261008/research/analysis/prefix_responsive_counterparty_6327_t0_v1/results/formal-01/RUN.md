# Formal allocation 01 — execution record

- Allocation: `PREFIX-RESPONSIVE-COUNTERPARTY-6327-T0-20261002-01`.
- Preregistration: Issue #6327 comment posted immediately before the candidate; source base `89f27caf1e9fcf3bc2c2c3c2db7d62ee6d19e4ae`.
- Candidate invocations: 1; independent auditor invocations: 1; retries: 0.
- Engine: OrbStack Docker Engine 29.4.0, Linux/aarch64, cgroup v2.
- Image ID: `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`python:3.12-slim`, linux/arm64).
- Isolation: network none, read-only root, all input mounts read-only, configured 1 CPU/256 MiB/64 PIDs, all capabilities dropped, no-new-privileges. Host-level hard memory enforcement is not claimed.

## Candidate command

```sh
docker run --rm --pull never --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/prefix_responsive_counterparty_6327_t0_v1/candidate.py,dst=/src/candidate.py,readonly \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/prefix_responsive_counterparty_6327_t0_v1/fixture.json,dst=/src/fixture.json,readonly \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/prefix_responsive_counterparty_6327_t0_v1/calibration.json,dst=/src/calibration.json,readonly \
  --tmpfs /tmp:rw,noexec,nosuid,size=8m \
  sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python /src/candidate.py /src/fixture.json /src/calibration.json
```

stdout bytes are `candidate.raw.json`; stderr is `candidate.stderr.txt`; status is `candidate.exit`.

## Independent raw-only auditor command

```sh
docker run --rm --pull never --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/prefix_responsive_counterparty_6327_t0_v1/audit.py,dst=/src/audit.py,readonly \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/prefix_responsive_counterparty_6327_t0_v1/fixture.json,dst=/src/fixture.json,readonly \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/prefix_responsive_counterparty_6327_t0_v1/calibration.json,dst=/src/calibration.json,readonly \
  --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/issue-6331-wake-fence-t0/research/analysis/prefix_responsive_counterparty_6327_t0_v1/results/formal-01/candidate.raw.json,dst=/src/candidate.raw.json,readonly \
  --tmpfs /tmp:rw,noexec,nosuid,size=8m \
  sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python /src/audit.py /src/fixture.json /src/calibration.json /src/candidate.raw.json
```

stdout bytes are `audit.raw.json`; stderr is `auditor.stderr.txt`; status is `auditor.exit`. Auditor container received no candidate source.

## Captured outcome

- Candidate exit 0, 64 rows, stderr empty.
- Auditor exit 0, exact 64/64 reconstruction, replay provenance/frequency check true, all five mutations rejected, stderr empty.
- Exact hashes are in the parent `SHA256SUMS`.
