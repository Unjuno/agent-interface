# Excluded construction check

OrbStack 29.4.0 / linux-arm64, pinned image
`sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
The checkout was mounted read-only at `/repo`; this study directory was mounted
separately read-only at `/study`. Root filesystem was read-only, network none,
1 CPU, 256 MiB memory and swap, 32 PIDs, all capabilities dropped,
no-new-privileges, and a 16 MiB noexec/nosuid `/tmp`.

The exact construction command exited 0:

```sh
docker --context orbstack run --rm --pull=never --platform linux/arm64 \
  --network none --read-only --cpus=1 --memory=256m --memory-swap=256m \
  --pids-limit=32 --cap-drop=ALL --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --workdir /repo \
  --mount type=bind,source=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/agent-interface-obstac-3850/work/issue-3924-orbstac-broker-currentmain-20260926,target=/repo,readonly \
  --mount type=bind,source=/Users/taka/Documents/Codex/2026-09-19/new-chat/work/agent-interface-obstac-3850/work/issue-3924-orbstac-broker-currentmain-20260926/research/integration/issue_3924_broker_exit_contract_v2,target=/study,readonly \
  sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python /repo/research/integration/issue_3924_broker_exit_contract_v2/construction_check.py
```

Output:

```text
CONSTRUCTION_CHECK PASS study_mount=present fake_executable=executable source_hashes=2 formal_cases=0 broker_invocations=0 fake_invocations=0 real_codex=absent
```

This confirms only the source/mount/runner construction. No broker or fake
process was invoked; the formal allocation count remains 0.
