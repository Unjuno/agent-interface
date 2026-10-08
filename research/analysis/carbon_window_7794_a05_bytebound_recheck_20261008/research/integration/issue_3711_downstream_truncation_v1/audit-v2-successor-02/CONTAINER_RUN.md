# Container run — corrected audit successor 02

The audit consumed `/src` source read-only and `/evidence` (`formal-02/`) read-only. Only `/out` was writable. It ran with `--network none`, `--read-only`, `--cap-drop ALL`, `no-new-privileges`, pinned Python 3.12 image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, and a bounded tmpfs.

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,exec,size=64m --pids-limit 16 --memory 256m --cpus 1 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,source="$PWD",target=/src,readonly \
  --mount type=bind,source="$PWD/research/integration/issue_3711_downstream_truncation_v1/formal-02",target=/evidence,readonly \
  --mount type=bind,source="$PWD/research/integration/issue_3711_downstream_truncation_v1/audit-v2-successor-02/result",target=/out \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python /src/research/integration/issue_3711_downstream_truncation_v1/audit-v2-successor-02/audit.py /evidence /out
```

Exit 0; `PASS_V2_ARTIFACT_BINDING`; errors `[]`. The machine-readable result is `result/RESULT.json`.
