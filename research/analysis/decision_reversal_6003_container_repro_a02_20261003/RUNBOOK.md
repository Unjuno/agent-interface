# #6003 successor A02 — namespace-safe OrbStack reproduction

**Allocation:** `6003-container-repro-a02-20261003`
**Parent:** #6744, successor to failed A01 #6740
**Integration branch:** `research/6003-container-repro-a01-20261003`
**Evidence path:** `research/analysis/decision_reversal_6003_container_repro_a02_20261003/`
**Frozen base:** `e52c4a65915cf48641c63cc95950be15f1b77cbf`
**Runtime:** OrbStack Docker Engine 29.4.0, linux/arm64
**Image:** `python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`, already local.

## Frozen materials and hypothesis

The FREEZE.json, selector and auditor are byte-identical to #6740 A01; their hashes must be rechecked before launch and stored in the execution record. A01 remains a failed runner/import collision and contributes no selector result.

**H:** Running those exact files with `sys.path[0] = "/"` and a current working directory of `/` prevents `/tmp/run/select.py` from shadowing Python's standard-library `select`, allowing candidate/auditor to reproduce the host predecessor's result and controls.

**T:** One candidate, then one independent mathematical auditor, each in a distinct pinned local image container; `--pull=never --network=none --read-only`; one CPU, 256 MiB, 64 PIDs, all capabilities dropped, no-new-privileges, non-root UID 1000, and 16 MiB tmpfs. Use no model, GUI, GPU, package install, image pull/build, retries, tuning, or shared-container access.

**D:** PASS only if the candidate and auditor both exit 0, independent errors are empty, cheapest and nominal entropy choose A, robust reversal chooses B, the B/C entropy order reverses under the declared prior shift, null is UNRANKABLE, mandatory sentinel remains, STOP is excluded, and all rankings/control values equal the host predecessor. Any failed invocation is terminal for A02.

**C:** One synthetic finite table, one OrbStack arm64 host, one local pinned Python image, one candidate/auditor pair.

**U:** Synthetic method reproducibility only; no calibrated prior, roadmap-productivity, GUI/runtime, safety-effectiveness, or broad-portability claim.

## Container command shape

Both commands run from `/` and explicitly replace `sys.path[0]` before executing the file by absolute path. This avoids the #6740 A01 failure without changing candidate or auditor source. The final `sha256sum` and delimited `cat` preserve the exact tmpfs result through container stdout before the container stops.

Candidate:

```sh
docker run --name issue6744-candidate-a02 --pull=never --network=none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user 1000:1000 --workdir / --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-03/agent-interface-6003-container-repro-a01-20261003/research/analysis/decision_reversal_6003_container_repro_a02_20261003,dst=/input,readonly --entrypoint /bin/sh python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b -c 'mkdir -p /tmp/run && cp /input/FREEZE.json /input/select.py /input/audit.py /tmp/run/ && cd / && python -B -c "import sys; from pathlib import Path; sys.path[0]=\"/\"; p=\"/tmp/run/select.py\"; exec(compile(Path(p).read_bytes(),p,\"exec\"),{\"__name__\":\"__main__\",\"__file__\":p})" && sha256sum /tmp/run/candidate_result.json && printf "\\nCANDIDATE_JSON_BEGIN\\n" && cat /tmp/run/candidate_result.json && printf "\\nCANDIDATE_JSON_END\\n"'
```

Retain the complete `docker logs` stdout and extract the bytes between the candidate markers as `execution/candidate_result.json`. The hash printed immediately before the marker must match those extracted bytes.

Auditor (separate container, candidate result mounted read-only):

```sh
docker run --name issue6744-auditor-a02 --pull=never --network=none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user 1000:1000 --workdir / --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-03/agent-interface-6003-container-repro-a01-20261003/research/analysis/decision_reversal_6003_container_repro_a01_20261003,dst=/input,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-03/agent-interface-6003-container-repro-a01-20261003/research/analysis/decision_reversal_6003_container_repro_a02_20261003/execution,dst=/evidence,readonly --entrypoint /bin/sh python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b -c 'mkdir -p /tmp/audit && cp /input/FREEZE.json /input/select.py /input/audit.py /tmp/audit/ && cp /evidence/candidate_result.json /tmp/audit/ && cd / && python -B -c "import sys; from pathlib import Path; sys.path[0]=\"/\"; p=\"/tmp/audit/audit.py\"; exec(compile(Path(p).read_bytes(),p,\"exec\"),{\"__name__\":\"__main__\",\"__file__\":p})" && sha256sum /tmp/audit/independent_audit.json && printf "\\nAUDIT_JSON_BEGIN\\n" && cat /tmp/audit/independent_audit.json && printf "\\nAUDIT_JSON_END\\n"'
```

Retain full stdout and extract the delimited independent audit JSON. Do not use `docker cp` after exit: tmpfs is ephemeral. Record exact container IDs/settings and remove only these named stopped containers after both logs and extracted JSON hashes are verified.

## Construction / no-run checks

`test_construction.py` checks only frozen hashes, fixture structure and syntax; it does not import or execute candidate/auditor logic. Before candidate launch, the allocation had formal candidate/audit counts 0/0.

## A02 actual disposition

The candidate and mathematical auditor each ran once and exited 0. The namespace-safe `python -B -c` entrypoint kept the execution directory off the module search path, avoiding the #6740 A01 local-`select.py` collision. Both JSON outputs were emitted to container stdout with in-container SHA-256, retained in `execution/`, and independently hash-checked. The auditor returned `PASS_CONTAINER_REPRODUCTION_METHOD`, errors empty; the full selector values and predecessor comparison are in `execution/PARITY_CHECK.json`.
