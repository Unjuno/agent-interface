# Exact formal container invocation

The one-shot container process completed with exit 0 and emitted:

```json
{"allocation":"issue3752-request-temp-crash-successor-02","disposition":"PASS_SCOPED_REQUEST_TEMP_UNKNOWN_NO_REPLAY","errors":[]}
```

Command (the empty host output directory was `/tmp/issue3752-successor02-formal.0OwYqD`; source was this branch checkout):

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,exec,size=64m --pids-limit 32 --memory 512m --cpus 1 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,source="$PWD",target=/src,readonly \
  --mount type=bind,source=/tmp/issue3752-successor02-formal.0OwYqD,target=/out \
  --env SOURCE_ROOT=/src \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python /src/research/integration/issue_3752_request_temp_crash_v2/experiment.py /out
```

Only the mounted output directory was writable. Raw output and exact temp bytes are retained beside this file; `inputs/` contains the exact synthetic CLI request inputs. The runtime image/source were not changed by the container.
