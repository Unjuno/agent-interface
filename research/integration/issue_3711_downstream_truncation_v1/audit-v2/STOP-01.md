# Audit v2-01 — STOP, provenance-field mismatch

The artifact audit completed but returned `FAIL_AUDIT_V2` with the single error `ALLOCATION_OR_BASE_MISMATCH`. Its freeze incorrectly used the later audit-code base (`e6f74d3b9fef0467327823ab97cb15f0dbe59ac4`) as the formal experiment base, while the raw allocation correctly records its frozen experiment source as `2dff80852292cc82fd5c23a449c8244bea94bc25`.

It ran in pinned Python 3.12 `linux/arm64` with `--network none`, `--read-only` container root, and source mounted read-only. The formal-02 directory was the writable bind mounted at `/out` so the auditor could write its result under `audit-v2/formal-02-recheck/`; the later successor audit improves this by mounting the formal evidence separately read-only and writing to a distinct output mount. The first audit exited 1. The raw, v1 audit, formal freeze, request, and report hashes were checked afterward and remained unchanged.

Exact command:

```sh
docker run --rm --name issue3711-downstream-truncation-auditv2 --platform linux/arm64 \
  --network none --read-only --tmpfs /tmp:rw,exec,size=64m --pids-limit 16 \
  --memory 256m --cpus 1 --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,source="$PWD",target=/src,readonly \
  --mount type=bind,source="$PWD/research/integration/issue_3711_downstream_truncation_v1/formal-02",target=/out \
  --env PYTHONPATH=/src \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python /src/research/integration/issue_3711_downstream_truncation_v1/audit-v2/audit.py /out /src
```

No source or evidence files were modified; the failure result remains at `formal-02-recheck/RESULT.json`. This is an audit harness provenance-field error, not a contradiction in formal-02's experimental observations. Audit v2-01 will not be rerun. A distinct successor audit separates the formal-source base from the audit-code base and rechecks the retained evidence.
