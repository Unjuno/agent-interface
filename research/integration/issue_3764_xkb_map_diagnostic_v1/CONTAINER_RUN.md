# Formal command (run only after GitHub preregistration)

Use a fresh, empty output directory and the exact frozen source checkout. Do not rerun under this allocation identity.

```sh
output="$(mktemp -d /tmp/issue3764-map-diagnostic-01.XXXXXX)"
test -z "$(find "$output" -mindepth 1 -print -quit)"
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,exec,size=64m --pids-limit 32 --memory 512m --cpus 1 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,source="$PWD",target=/src,readonly \
  --mount type=bind,source="$output",target=/out \
  agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  /src/research/integration/issue_3764_xkb_map_diagnostic_v1/runner.py /out
```

The image entrypoint is `python3`; the command above passes the runner as its argument. Preserve the container stdout/exit status separately from runner raw output and later audit logs. The independent auditor must receive evidence and source as read-only mounts and write to a different initially empty output directory.
