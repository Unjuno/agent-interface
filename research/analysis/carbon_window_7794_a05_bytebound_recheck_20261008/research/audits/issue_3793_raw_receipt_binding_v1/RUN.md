# Frozen one-shot command

Host preflight: OrbStack Docker 29.4.0, linux/aarch64. Execution uses `--pull=never` and `--network none`; the image must already exist locally.

```sh
docker run --rm --pull=never --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --pids-limit 16 --memory 256m --cpus 1 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,source="$PWD/research/audits/issue_3793_raw_receipt_binding_v1/input",target=/in,readonly \
  --mount type=bind,source="$PWD/research/audits/issue_3793_raw_receipt_binding_v1/audit.py",target=/audit.py,readonly \
  --mount type=bind,source="$PWD/research/audits/issue_3793_raw_receipt_binding_v1/output",target=/out \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python /audit.py /in /out
```

The gate requires a clean baseline and specific raw receipt mismatch codes for both corruptions. Do not retry this allocation; infrastructure/container failure is STOP.
