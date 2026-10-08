# Exact executed commands

All container invocations used the local image digest from `FREEZE.json`; no pull, build, package install, or network access was used. The host shell was zsh. Candidate and auditor attached streams were captured with `tee`; each result JSON was then extracted verbatim from the named sentinels in that retained stream. Candidate/auditor were not rerun.

## Construction

```sh
docker run --pull=never --name issue6342-t0-construction-20261003 --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user=1000:1000 --workdir=/ --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-03/agent-interface-6342-safe-stop-t0-orbstack-20261003/research/analysis/reactance_safe_stop_6342_t0_20261003,dst=/input,readonly --tmpfs /tmp:rw,noexec,nosuid,size=16m python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b python -B -m unittest discover -s /input -p 'test_*.py' -v 2>&1 | tee research/analysis/reactance_safe_stop_6342_t0_20261003/execution/construction.stdout.log
```

## Candidate (one invocation)

```sh
set -o pipefail
docker run --pull=never --name issue6342-t0-candidate-20261003 --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user=1000:1000 --workdir=/ --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-03/agent-interface-6342-safe-stop-t0-orbstack-20261003/research/analysis/reactance_safe_stop_6342_t0_20261003,dst=/input,readonly --tmpfs /tmp:rw,noexec,nosuid,size=16m --entrypoint=/bin/sh python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b -c 'set -eu; for f in memory.max memory.swap.max cpu.max pids.max; do printf "CGROUP_%s=" "$f"; if [ -r "/sys/fs/cgroup/$f" ]; then cat "/sys/fs/cgroup/$f"; else printf "UNAVAILABLE\n"; fi; done; python -B /input/render_cards.py --fixture /input/cards.json --output /tmp/candidate.json; printf "===CANDIDATE_JSON_BEGIN===\n"; cat /tmp/candidate.json; printf "===CANDIDATE_JSON_END===\n"' 2>&1 | tee research/analysis/reactance_safe_stop_6342_t0_20261003/execution/candidate.stdout.log
```

## Independent auditor (one invocation)

```sh
set -o pipefail
docker run --pull=never --name issue6342-t0-auditor-20261003 --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user=1000:1000 --workdir=/ --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-03/agent-interface-6342-safe-stop-t0-orbstack-20261003/research/analysis/reactance_safe_stop_6342_t0_20261003,dst=/input,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-03/agent-interface-6342-safe-stop-t0-orbstack-20261003/research/analysis/reactance_safe_stop_6342_t0_20261003/execution/candidate.json,dst=/evidence/candidate.json,readonly --tmpfs /tmp:rw,noexec,nosuid,size=16m --entrypoint=/bin/sh python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b -c 'set -eu; for f in memory.max memory.swap.max cpu.max pids.max; do printf "CGROUP_%s=" "$f"; if [ -r "/sys/fs/cgroup/$f" ]; then cat "/sys/fs/cgroup/$f"; else printf "UNAVAILABLE\n"; fi; done; python -B /input/audit_cards.py --candidate /evidence/candidate.json --output /tmp/audit.json; printf "===AUDIT_JSON_BEGIN===\n"; cat /tmp/audit.json; printf "===AUDIT_JSON_END===\n"' 2>&1 | tee research/analysis/reactance_safe_stop_6342_t0_20261003/execution/auditor.stdout.log
```

## Result extraction (host-side, no experiment process rerun)

```sh
sed -n '/^===CANDIDATE_JSON_BEGIN===$/,/^===CANDIDATE_JSON_END===$/{/^===CANDIDATE_JSON_BEGIN===$/d;/^===CANDIDATE_JSON_END===$/d;p;}' research/analysis/reactance_safe_stop_6342_t0_20261003/execution/candidate.stdout.log > research/analysis/reactance_safe_stop_6342_t0_20261003/execution/candidate.json
sed -n '/^===AUDIT_JSON_BEGIN===$/,/^===AUDIT_JSON_END===$/{/^===AUDIT_JSON_BEGIN===$/d;/^===AUDIT_JSON_END===$/d;p;}' research/analysis/reactance_safe_stop_6342_t0_20261003/execution/auditor.stdout.log > research/analysis/reactance_safe_stop_6342_t0_20261003/execution/audit.json
```
