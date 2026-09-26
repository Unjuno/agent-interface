# Allocation 02 commands

Both commands used the pinned local `python:3.12-slim` image with
`--pull=never --platform linux/arm64 --network none --read-only --cpus=1
--memory=256m --memory-swap=256m --pids-limit=32 --cap-drop=ALL
--security-opt no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=16m`.
The full checkout was mounted read-only at `/repo`; only the dedicated
`formal_run_02` evidence directory was writable at `/evidence`.

Formal matrix:

```sh
docker --context orbstack run --rm --pull=never --platform linux/arm64 \
  --network none --read-only --cpus=1 --memory=256m --memory-swap=256m \
  --pids-limit=32 --cap-drop=ALL --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m \
  --mount type=bind,source=$CHECKOUT,target=/repo,readonly \
  --mount type=bind,source=$EVIDENCE,target=/evidence \
  python:3.12-slim python /repo/research/integration/issue_3924_orbstac_broker_contract_v1/formal_runner_02.py
```

Independent audit used a separate fresh container with the same limits and
network setting, mounting `$CHECKOUT` read-only at `/study` and `$EVIDENCE`
read-write at `/evidence`, then running:

```sh
python /study/research/integration/issue_3924_orbstac_broker_contract_v1/audit.py
```

The formal container command omitted the required read-only `$CHECKOUT` mount
at `/study`, although the runner's frozen fake path was `/study/fake_codex.py`.
The resulting provenance STOP and all raw outputs are retained under
`formal_run_02/formal/`. No formal case is repeated in this allocation.
