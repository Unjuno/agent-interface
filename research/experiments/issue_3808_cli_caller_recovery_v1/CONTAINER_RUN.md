# Formal-01 reproduction record

Base: `ddb311528e96e2a613dd660f8cb24b14f413081d`
Container engine: OrbStack Docker `29.4.0`, Linux/arm64
Image: `python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`
Network: disabled
Root/source: read-only
Limits: 1 CPU, 512 MiB, 64 PIDs, all capabilities dropped, no-new-privileges
Formal raw: `results/formal-01/raw.json`, SHA-256 `07b761e6c9c4f03c5cce3fdc2f64bdc7017da3d97e6f30a9ac312a3b418b902f`
Audit: `results/formal-01/audit.json`, SHA-256 `799cd2f12527f53334a266f8070138893981a37bc8ab99e3e420ef9dfb843983`

The formal output directory and independent-audit output directory were separately created empty before their respective container invocations. The frozen formal runner ran once; the frozen raw-only auditor ran once in a second container with evidence mounted read-only. Both output files were copied byte-for-byte into this committed evidence path and compared with their external-output originals.

## Formal runner command

Run from the repository root with an already-created empty `/tmp/issue3808-formal-01-raw` directory:

```sh
docker --context orbstack run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m --cpus 1 --memory 512m --pids-limit 64 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount "type=bind,src=$PWD,dst=/source,readonly" \
  --mount type=bind,src=/tmp/issue3808-formal-01-raw,dst=/out \
  --workdir /source -e PYTHONPATH=/source -e OUT=/out \
  --entrypoint python3 \
  python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  /source/research/experiments/issue_3808_cli_caller_recovery_v1/runner.py
```

Captured result: exit 0; `PASS_CALLER_RECOVERS_AFTER_DOWNSTREAM_TRUNCATION_SCOPED`, 4 rows, raw SHA-256 as above.

## Independent audit command

Run from the repository root with the formal raw directory read-only and a separately created empty `/tmp/issue3808-audit-01` directory:

```sh
docker --context orbstack run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m --cpus 1 --memory 512m --pids-limit 64 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount "type=bind,src=$PWD,dst=/source,readonly" \
  --mount type=bind,src=/tmp/issue3808-formal-01-raw,dst=/evidence,readonly \
  --mount type=bind,src=/tmp/issue3808-audit-01,dst=/out \
  --workdir /source -e EVIDENCE=/evidence/raw.json -e OUT=/out \
  --entrypoint python3 \
  python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  /source/research/experiments/issue_3808_cli_caller_recovery_v1/audit.py
```

Captured result: exit 0; `PASS_AUDIT_CALLER_RECOVERY_SCOPED`, errors `[]`, four rows, raw SHA-256 matched. Audit JSON SHA-256 as above.
