# T8 run log

Allocation `SEMANTIC-RECEIPT-5442-T8-ORBSTACK-20261002-01`; base `49144844b482026c33fcfbde7e2fd5f7bdc7762c`; see `FREEZE.json` for frozen inputs.

## Construction

- Initial host command: `python3 -m unittest discover -s research/analysis/semantic_receipt_target_binding_5442_t8 -p 'test_*.py' -v`. Result: 5 passed, 1 failed because auditor hash checks correctly rejected the still-placeholder `PENDING` hashes in the not-yet-frozen file. This was a construction-stage setup failure; neither formal program ran.
- After replacing all placeholders with source SHA-256 values, the same command passed 6/6. `git diff --check` passed. Candidate/auditor hashes were checked again immediately before preregistration and formal run.
- Runtime preflight: `docker version --format 'client={{.Client.Version}} server={{.Server.Version}} os={{.Server.Os}} arch={{.Server.Arch}}'` → client 29.5.2, server 29.4.0, Linux arm64. The pinned image was already cached; `docker image inspect python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` reported Linux/arm64, and one preflight `docker run --rm --network none --read-only --entrypoint python <same-digest> --version` printed Python 3.12.14. This version check did not invoke candidate or auditor code.
- Conflict check: no container name beginning `unjuno-5442-t8` existed. The unrelated `unjuno-native-ci-6092` was sampled at 0.00% CPU / 112 KiB and left running, untouched.

## Formal candidate — one invocation

Exact create command (source path is the T8 package directory):

```text
docker create --pull=never --name unjuno-5442-t8-candidate --platform linux/arm64 --network none --read-only --cpus=1 --memory=256m --pids-limit=32 --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/unjuno-agent-interface-github-mcp-main/work/semantic-receipt-5442-target-binding-t8/research/analysis/semantic_receipt_target_binding_5442_t8,dst=/src,readonly --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/candidate.py
docker start --attach 2c38675a9421dc5ced82908f2346e6fde0c437df41fbc255564e0a4cee515cbd > formal_01/candidate.raw.json 2> formal_01/candidate.stderr.txt
```

Exit 0; container inspected as `exited`, `OOMKilled=false`. Started `2026-10-02T07:01:22.330258054Z`, finished `2026-10-02T07:01:22.742576306Z`. Inspected settings: `NetworkMode=none`, `ReadonlyRootfs=true`, `NanoCpus=1000000000`, `Memory=268435456`, `PidsLimit=32`, configured user `65534:65534`; `/src` mount `RW=false`. Candidate stderr is empty. Raw SHA-256 `14822a774c5bdd42d6daf880072eb83208d058c93240ec9e8de5304ffecbce37`.

## Independent auditor — one invocation after candidate exit 0

Exact create command:

```text
docker create --pull=never --name unjuno-5442-t8-auditor --platform linux/arm64 --network none --read-only --cpus=1 --memory=256m --pids-limit=32 --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/unjuno-agent-interface-github-mcp-main/work/semantic-receipt-5442-target-binding-t8/research/analysis/semantic_receipt_target_binding_5442_t8,dst=/src,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/unjuno-agent-interface-github-mcp-main/work/semantic-receipt-5442-target-binding-t8/research/analysis/semantic_receipt_target_binding_5442_t8/formal_01/candidate.raw.json,dst=/input/candidate.raw.json,readonly --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/audit.py /input/candidate.raw.json
docker start --attach 65284ef22bd5db7ac03a53797f3848270d3c7651ec489bb4569edc23c583eb7d > formal_01/audit.json 2> formal_01/auditor.stderr.txt
```

Exit 0; container inspected as `exited`, `OOMKilled=false`. Started `2026-10-02T07:01:57.39792315Z`, finished `2026-10-02T07:01:57.810142233Z`. The same network/read-only/CPU/memory/PID/user settings were inspected; both mounts had `RW=false`. Auditor stderr is empty. Audit SHA-256 `68f2ab03bdcf81f0f69509e3db1d4411749d0de259f73870fe8dc2794611f656`.

## Auditor output

`PASS_TARGET_BINDING_SCOPED`; rows checked 4; errors `[]`; rejected controls: actual nested intent target=true, endpoint target=true, semantic decision=true, missing row=true, duplicate row=true, scenario-source intent target=true. No candidate/auditor retry or post-hoc correction.

After both complete inspect receipts had been saved, the two exited T8-only containers were removed by exact ID (`docker rm 2c38675a9421dc5ced82908f2346e6fde0c437df41fbc255564e0a4cee515cbd 65284ef22bd5db7ac03a53797f3848270d3c7651ec489bb4569edc23c583eb7d`). The unrelated active container remained untouched.
