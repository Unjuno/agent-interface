# Direct-Xvfb pre-task ready probe

This distinct setup allocation checks whether starting Xvfb directly and
polling its display with `xdpyinfo` avoids the `xvfb-run` readiness-signal
intervention seen in `ready-gate-01`. It preserves that earlier HOLD unchanged.

## H / T / D / C / U

- **H** — With the same hash-pinned historical route and cached runtime, a
  directly started Xvfb whose display responds to `xdpyinfo` allows the
  Chromium session wrapper to emit one `ready` event without manual signal
  intervention.
- **T** — Allocation `issue2922-direct-xvfb-ready-20260927-r1`, seed `992924`,
  output namespace `ready-gate-03`; source commit
  `01349d7bc76e5635f5568c53ffeec4d9ff49abb1`; image
  `issue-2849-task1-runtime:v3-20260921`,
  `sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393`
  (`linux/arm64`). Network disabled; root read-only; source mounted
  read-only; bounded `/tmp` and `/dev/shm`. Xvfb was started directly and
  `xdpyinfo -display :99` polled before starting the session. Openbox and
  Chromium ran privately in the container. Only `finish` was supplied after
  startup. The container exit code was 0.
- **D** — One `ready` event; one exact initial observation; `about:blank -
  Chromium`; command `finish`; evaluator reports missing output as expected
  with no task action; manual Xvfb signal interventions: zero. Disposition:
  `PASS_PRETASK_READY_ONLY`.
- **C** — Synthetic private container only; no external network, model/provider,
  user desktop, physical input, task allocation, submit, or task effect. The
  route exposed a private endpoint at `http://127.0.0.1:34321/`, but Chromium
  did not request it and remained on `about:blank`.
- **U** — This validates the direct-Xvfb harness plus pre-task ready event for
  this cached image/source pair. It does not prove a clean `xvfb-run`
  handshake, fixture navigation/request, broker/IPC behavior, task success, or
  production/integrated runtime behavior.

## Raw evidence

`ready_gate_03/` retains the exact event log, stdout, source receipt, setup
diagnostics, screenshot, image artifact, and direct-Xvfb script. SHA-256:

- events: `55a7a44b193dfdc857e7fd9f67902603dc6040c1b15d6ded27d45b644ee4f972`
- source receipt: `fde3db622828fd5d22326590acf06d0fbd69fea36762926d522cc2570ae65a55`
- screenshot: `438a88df239b6bf09b2c16649456735451300a032bd48b75b676a3b27414746d`
- `.ait` image artifact: `5af98475ee8d76109564ef0cb0784f4b38b938807ee64861438a08827cd5bee5`
- setup diagnostics: `8e3db63f0502051fc0c47c3fd8806f439b58c95f9002db4764448543a6648241`
- harness stdout: `72f8c331a721598fae4b33ce570b98f363369416a4f0f50ce0fe9f7908c71b8d`
- direct-Xvfb script: `4c7f2e5cc68a31410b06d0bf8f94878073485d20c2dfe843cfcfe962dab12a2c`
- predecessor setup STOP: `97a9ee6720d6bb86e1aa3b8b6473c759b54c7d403f74fbd2d704ae5cdfd8795b`

The previous, distinct seed `992923` stopped before the session started because
the host pre-created `ready-gate-02`, conflicting with the runner's
`exist_ok=False` output-directory creation. That harness mistake is retained in
`READY_GATE_03_RESULT.json`; seed and namespace were not reused.

## Reproduction command

```sh
docker run --rm -i --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m \
  --tmpfs /dev/shm:rw,nosuid,nodev,size=128m \
  --mount type=bind,src=<package>/source_snapshot/research,dst=/repo/research,readonly \
  --mount type=bind,src=<fresh-evidence-parent>,dst=/evidence \
  --mount type=bind,src=<package>/ready_gate_03/run-direct-xvfb.sh,dst=/experiment/run.sh,readonly \
  --workdir /repo/research/live_control \
  --env PYTHONPATH=/repo/research/live_control:/repo/research/observation_gating \
  --entrypoint /bin/bash issue-2849-task1-runtime:v3-20260921 /experiment/run.sh
```

The command above documents the consumed allocation identity; do not execute
it as written because it intentionally names seed `992924` and the already-used
`ready-gate-03` namespace.

Do not reuse seed `992923` or `992924`, nor output namespaces `ready-gate-02`
or `ready-gate-03`.
