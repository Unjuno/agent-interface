# Separate no-GUI import-only probe

This is a later, distinct setup rung. It does not replace the original
`HOLD_XVFB_READY_SIGNAL_INTERVENTION` startup observation and does not test a
GUI ready event, fixture request, broker/IPC behavior, or task effect.

## H / T / D / C / U

- **H** — With the hash-pinned #2730 source snapshot mounted at its expected
  paths and the historical import roots on `PYTHONPATH`, importing
  `session_v4` can complete without starting Xvfb or Chromium.
- **T** — One import-only container run, allocation
  `issue2922-no-gui-import-20260927-r1`, using source commit
  `01349d7bc76e5635f5568c53ffeec4d9ff49abb1` and cached image
  `issue-2849-task1-runtime:v3-20260921`
  (`sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393`).
  Network disabled, root and source read-only, bounded `/tmp`, no Xvfb wrapper,
  Chromium, task, or GUI command.
- **D** — Exit code 0; stdout marker `IMPORT_OK`; stderr empty. Disposition:
  `PASS_IMPORT_ONLY`.
- **C** — Synthetic import preflight only. No display server or browser was
  started by the command. No model/provider, task input, authority, output
  effect, or endpoint request was exercised.
- **U** — This proves imports complete in this cached image, not that the
  originally intended no-GUI entrypoint emits a runtime-ready event, that
  Xvfb handshakes cleanly, or that the route reaches its fixture/task effect.

The earlier `issue-3300-obstac-probe:v1` image still has a separate retained
STOP because `PIL` is unavailable there. This successful import used the
cached historical GUI runtime image without invoking its GUI components.

Reproduction command (replace `<package>` with this directory):

```sh
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --mount type=bind,src=<package>/source_snapshot/research,dst=/repo/research,readonly \
  --workdir /repo/research/live_control \
  --env PYTHONPATH=/repo/research/live_control:/repo/research/observation_gating \
  --entrypoint /usr/bin/python3 issue-2849-task1-runtime:v3-20260921 \
  -c 'import session_v4; print("IMPORT_OK")'
```
