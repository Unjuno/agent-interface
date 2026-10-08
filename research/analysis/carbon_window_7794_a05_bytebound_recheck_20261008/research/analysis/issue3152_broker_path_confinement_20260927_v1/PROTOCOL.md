# Issue #3152 current-main path-boundary preformal probe

## H

The current-main host broker's `host_path` mapper accepts a request path that resolves outside the declared repository (via a non-repository absolute path, `..`, or a symlink). If so, an untrusted container IPC request can select a host-side working directory or schema outside the intended repository boundary before model escalation.

## T — frozen, construction-only probe

- Source commit: `fc4159ddd0b546c2adfe58faf8d40771e6e5dfc3`.
- Broker: `runtime/host_model_ipc_broker_v1.py`, Git blob `5734f54f318db9ac5e96b2bed6f6bed105ac39ff`.
- Existing tests: `runtime/test_host_model_ipc_broker_v1.py`, Git blob `79405a089708a3f2d7c0982192592041125cf0dd`.
- Image: cached `ghcr.io/zaproxy/zaproxy:stable`, Linux/amd64 image ID `sha256:8d387b1a63e3425beef4846e39719f5af2a787753af2d8b6558c6257d7a577a2`; Python 3.11.2. Java in this image is irrelevant and no Java process is run.
- Run the exact current-main broker unit tests, then send a synthetic request through `serve()` whose `schema` is `/etc/passwd` and whose `/repo/link` working path is a symlink to a sibling directory outside the declared repo. Replace only `subprocess.run` with a recorder returning a fixed empty result; it must not invoke Codex, a model, or a provider.
- Docker: one invocation; `--network none`, read-only root, 2 CPUs, 2 GiB RAM, 128 PIDs, all capabilities dropped, no-new-privileges; `/tmp` is a 16 MiB private tmpfs for synthetic files only.
- No GUI, image, user data, model/provider call, task input/effect, or formal #3152 allocation.

## D

- `PASS_PATH_CONFINEMENT_GAP_REPRODUCED` if both exact source hashes match, all frozen current-main tests pass, and the mock recorder observes the outside schema and symlink-escaped working directory passed to the host CLI argument vector.
- `NO_GAP_REPRODUCED` if the exact source hashes match and the broker rejects or confines both paths before the mocked subprocess boundary.
- `STOP_SOURCE_OR_IMAGE_MISMATCH` if any source/image identity differs or the frozen test suite cannot run.

This is a prerequisite/construction result only; none of these outcomes satisfies or consumes #3152's formal held-out typed-versus-scalar model-escalation allocation.

## C / U

The subprocess is mocked, so the probe demonstrates argument construction, not a successful external file read or model disclosure. One Linux path-mapping run does not establish Windows path semantics, actual model/task impact, or production exploitability. Instruction/schema/image digest binding, required evidence-role admission, downstream reserve, and final recovery outcome remain outside this probe.
