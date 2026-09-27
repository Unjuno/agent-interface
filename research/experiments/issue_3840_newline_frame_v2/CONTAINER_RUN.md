# Allocation issue3814-jsonl-frame-02 — frozen commands

Frozen runtime-source base main: `5842cea6b16dde275f79caef3f09fdba828112e0`

This is a historical source snapshot, not current main. Later main commits updated `runtime/cli_v1/api.py`, `runtime/cli_v1/test_cli.py`, and other documentation/workflow paths. This allocation tests only the frozen source hashes listed in PLAN.md; it makes no claim about later CLI revisions.

Docker Engine: Docker Desktop 28.5.1, Linux/amd64

Runner/auditor image: `python@sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b`

Network: disabled

Source/root: read-only

Formal and audit outputs: distinct fresh host directories

The paths below are fixed for this allocation and must be absent before use:

```powershell
$repoPath = 'C:\Users\junny\Documents\Codex\2026-09-21\agent-interface-3808'
$formalPath = 'C:\Users\junny\Documents\Codex\2026-09-21\issue-3840-formal-02'
$auditPath = 'C:\Users\junny\Documents\Codex\2026-09-21\issue-3840-audit-02'
$imageRef = 'python@sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b'
```

## Read-only import preflight

This does not execute the runner or CLI command. It verifies the frozen image and import path before the one formal invocation:

```powershell
docker run --rm --network none --read-only `
  --tmpfs /tmp:rw,nosuid,nodev,size=64m --cpus 1 --memory 512m --pids-limit 64 `
  --cap-drop ALL --security-opt no-new-privileges `
  --mount "type=bind,source=$repoPath,target=/source,readonly" `
  --workdir /source -e PYTHONPATH=/source `
  --entrypoint python3 $imageRef `
  -c "import platform; import runtime.cli_v1.__main__; print(platform.machine() + '|cli_import_ok')"
```

## Formal runner — one invocation only

```powershell
docker run --rm --network none --read-only `
  --tmpfs /tmp:rw,nosuid,nodev,size=64m --cpus 1 --memory 512m --pids-limit 64 `
  --cap-drop ALL --security-opt no-new-privileges `
  --mount "type=bind,source=$repoPath,target=/source,readonly" `
  --mount "type=bind,source=$formalPath,target=/out" `
  --workdir /source -e PYTHONPATH=/source `
  -e EXPECTED_COMMIT=5842cea6b16dde275f79caef3f09fdba828112e0 `
  -e EXPECTED_RUNNER_SHA256=4183ba737fbdd927ad76284cb214051350610e36e82455f2b3f9fba29f67539e `
  -e EXPECTED_AUDITOR_SHA256=1db4219cf934c8f6e0e22b4f77e78a0866d0a404dd8c1ce1ae39b34bcfab9b39 `
  -e "IMAGE_REF=$imageRef" -e OUT=/out `
  --entrypoint python3 $imageRef `
  /source/research/experiments/issue_3840_newline_frame_v2/runner.py
```

## Independent raw-only audit — separate container

Run once only after the formal runner exits and `raw.json` is present. Mount formal evidence read-only and use the separate fresh audit output directory:

```powershell
docker run --rm --network none --read-only `
  --tmpfs /tmp:rw,nosuid,nodev,size=64m --cpus 1 --memory 512m --pids-limit 64 `
  --cap-drop ALL --security-opt no-new-privileges `
  --mount "type=bind,source=$repoPath,target=/source,readonly" `
  --mount "type=bind,source=$formalPath,target=/evidence,readonly" `
  --mount "type=bind,source=$auditPath,target=/out" `
  --workdir /source -e SOURCE=/source -e EVIDENCE=/evidence/raw.json `
  -e EXPECTED_COMMIT=5842cea6b16dde275f79caef3f09fdba828112e0 `
  -e EXPECTED_RUNNER_SHA256=4183ba737fbdd927ad76284cb214051350610e36e82455f2b3f9fba29f67539e `
  -e EXPECTED_AUDITOR_SHA256=1db4219cf934c8f6e0e22b4f77e78a0866d0a404dd8c1ce1ae39b34bcfab9b39 `
  -e "IMAGE_REF=$imageRef" -e OUT=/out `
  --entrypoint python3 $imageRef `
  /source/research/experiments/issue_3840_newline_frame_v2/audit.py
```

The formal allocation is never retried. Preserve exact stdout, exit status, raw and audit files; do not modify them after execution.
