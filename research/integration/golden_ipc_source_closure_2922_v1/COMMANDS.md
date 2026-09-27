# Executed commands and deviations

All commands were local. No image was pulled, package installed, remote
workflow run, model/provider called, or GUI input submitted.

## Obstac probe image

```sh
docker image inspect issue-3300-obstac-probe:v1 --format '{{.Id}} {{.Os}}/{{.Architecture}}'
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --mount type=bind,src=<historical-source-tree>,dst=/repo,readonly \
  --workdir /repo/research/live_control \
  --env PYTHONPATH=/repo/research/live_control:/repo/research/observation_gating \
  --entrypoint python issue-3300-obstac-probe:v1 \
  -c 'import session_v4'
```

Image ID `sha256:57ad79ade1fc4d961017fb46575af305b12dc552fa54ea9369c32733cc2017f9`,
linux/arm64. STOP before route import completed: `ModuleNotFoundError: No
module named 'PIL'`. No install or replacement image was attempted in this
probe.

## Historical route startup instance

The actual startup-only command was:

```sh
printf '%s\n' '{"op":"finish"}' | docker run --rm -i --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m \
  --tmpfs /dev/shm:rw,nosuid,nodev,size=128m \
  --mount type=bind,src=<historical-source-tree>,dst=/repo,readonly \
  --mount type=bind,src=<evidence-output>,dst=/evidence \
  --workdir /repo/research/live_control \
  --env PYTHONPATH=/repo/research/live_control:/repo/research/observation_gating \
  --entrypoint /usr/bin/xvfb-run issue-2849-task1-runtime:v3-20260921 \
  -a /usr/bin/python3 /repo/research/live_control/session_v4.py \
  --app chromium --seed 992922 --out /evidence/ready-gate-01 \
  --chromium /usr/bin/chromium
```

This invocation produced no output in the initial 30-second wait. The same
container remained alive with only `xvfb-run` and `Xvfb`; its output directory
did not yet exist. `xdpyinfo -display :99` then independently returned display
metadata. One `docker kill --signal=USR1 <container-id>` was sent to release
the wrapper's documented Xvfb-ready wait. The session then emitted `ready`,
one initial observation, processed the already-piped `finish`, and exited;
the `--rm` container disappeared and wrote the evidence bundle. This signal
intervention is the reason for the HOLD disposition. It is not hidden or
relabelled as a clean run.

The output was not a task result. The screenshot shows `about:blank`; the
`finish` evaluator found no submitted output file, as expected with zero task
commands. The setup-only allocation/output identity is consumed.

## Independent audit CI

```sh
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --mount type=bind,src=<package-tree>,dst=/repo,readonly \
  --workdir /repo/research/integration/golden_ipc_source_closure_2922_v1 \
  --entrypoint python issue-3300-obstac-probe:v1 -m unittest -v test_audit
```

Result before the separate no-GUI rung: 6/6 tests passed (one baseline plus
five mutation tests); after recording that rung, two additional tests cover
the import-only contract. The raw-only audit checks four event rows, eight
source files, and the separate import-only result. The raw mutations cover
ready identity, endpoint, submit, source digest, and event/input evidence.
No experiment output was regenerated for this audit.
