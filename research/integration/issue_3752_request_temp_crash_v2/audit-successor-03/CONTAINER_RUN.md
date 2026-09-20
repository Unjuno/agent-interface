# Independent audit container invocation

The one-shot audit container completed with exit 0 and emitted:

```json
{"disposition":"PASS_AUDIT_V3","errors":[]}
```

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,exec,size=64m --pids-limit 32 --memory 512m --cpus 1 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,source="$PWD",target=/source,readonly \
  --mount type=bind,source="$PWD/research/integration/issue_3752_request_temp_crash_v2/formal-02",target=/evidence,readonly \
  --mount type=bind,source=/tmp/issue3752-audit03.EJY3rC,target=/results \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python /source/research/integration/issue_3752_request_temp_crash_v2/audit-successor-03/audit.py \
  /evidence /source /results
```

The only writable mount was the separate initially empty audit-results directory. Retained `audit.json` is copied unchanged alongside this record.
