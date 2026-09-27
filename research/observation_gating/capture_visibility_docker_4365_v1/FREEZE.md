# Frozen protocol — Docker replication of #4365

- Issue: #4827, allocation `capture-visibility-docker-4365-20260927-01`
- Intake main: `ca38c41b06d20785ffb0a6163a6a22034511c004`
- Branch: `research/capture-visibility-docker-4365-20260927`
- Evidence path: `research/observation_gating/capture_visibility_docker_4365_v1/`
- Allocation: exactly 12 new formal Xvfb sessions, six ordered conditions × two reps; no random seed; one producer orchestration, no replacements/retries.
- Parent study #4365 / merged PR #4385 remain unchanged. This measures only pinned-Docker environment transfer.

## H/T/D/C/U

**H:** On pinned Docker/Xvfb, the #4365 scoped boundary reproduces: native capture/IsViewable/VisibilityNotify alone are insufficient for parent-only region clearance in covered layouts; exact direct-child geometry plus native parent visibility yields UNKNOWN on all eight covered sessions, while four CLEAR/RESTORED sessions are CLEAR.

**T:** Use exact merged #4385 capture adapter (Git blob `2124f531f3b344b6aafed243b2d711baa78b7cbd`) and assessor (`21bfc2c83d70ef9b69cd214d193705bd4837ecf6`), plus only `runner.py` and independent stdlib `audit.py`. Conditions CLEAR, SIBLING_HALF, SIBLING_FULL, CHILD_HALF, CHILD_FULL, RESTORED, each in two fresh authenticated TCP-disabled Xvfb servers. Screen 640×480×24; parent [43,57,120,80]. Preserve both exact parent-window and root-screen XGetImage bytes and full format metadata. Construction01 is excluded; see CONSTRUCTION.md.

**D:** PASS only for 12 complete cases, 24 captures, 4 CLEAR/8 UNKNOWN assessor decisions, exact independent root-rectangle composition, no false-clear, only the preregistered SIBLING_FULL parent-window TypeError if any, exact source/image identity, neutral cleanup, and separate raw auditor errors=[]. Complete contradictory behavior is FAIL. Missing image/source/event/raw/cleanup/audit evidence is STOP; no retry.

**C:** Fixed opaque same-depth rectangles; one cached image, Python-Xlib 0.33, one Xvfb build. The raw auditor is stdlib-only, independent of runner and assessor. No model, input, host display, user data, GPU or network.

**U:** No compositor/alpha/Shape/offscreen/mixed-depth/concurrency/general toolkit, runtime adoption, model/task success, natural failure rate, performance or product claim.

## Frozen source identities

Local-byte SHA-256 is in `source_sha256.json`. The first two files' Git blob IDs identify the exact merged source. Image: `agent-interface-gtk-fixture-v3:local-main-2913`, immutable ID `sha256:acf83a1dfafd43c44d81e2f28f85fc844fa43dc73f36b689a862dd924f9235d0`, linux/amd64; Python 3.11.16; Python-Xlib 0.33; `/usr/bin/Xvfb` and `/usr/bin/xauth`. No pull/install.

## Formal commands

On the local Windows workspace, resolve `$src` to this frozen source directory and `$out` to a newly created empty `run-output/formal01`. Capture the full producer command/stdout/stderr in `CONTAINER_EXECUTION.txt`, preserve `docker inspect` after exit, then remove only this named stopped container. The Docker invocation is exactly:

```powershell
docker run --name capture-visibility-4827-formal01 --pull=never --network none --read-only --cpus=1 --memory=1g --pids-limit=64 --tmpfs /tmp:rw,nosuid,size=512m -v "${src}:/src:ro" -v "${out}:/out:rw" -w /src --entrypoint /usr/local/bin/python3 agent-interface-gtk-fixture-v3:local-main-2913 -B /src/runner.py /out
```

After preserving the producer exit and container inspection, run the auditor once in its own container. Preserve the auditor exit/log and inspect receipt; remove only this named stopped container:

```powershell
docker run --name capture-visibility-4827-audit01 --pull=never --network none --read-only --cpus=1 --memory=1g --pids-limit=64 --tmpfs /tmp:rw,nosuid,size=512m -v "${src}:/src:ro" -v "${out}:/out:rw" -w /src --entrypoint /usr/local/bin/python3 agent-interface-gtk-fixture-v3:local-main-2913 -B /src/audit.py --root /out --source /src --manifest /src/source_sha256.json --out /out/AUDIT.json
```

No CI/workflow is used as scientific execution.
