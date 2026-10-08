# Issue #3152 path-boundary preformal probe v2

This is a new construction probe after v1 stopped before scoring. Preserve v1's exact Git-blob derivation implementation stop and its unittest-discovery package-layout stop unchanged. Neither consumed nor altered the formal #3152 allocation.

## H

The exact current-main host broker's unvalidated container-to-host path mapping permits a synthetic IPC request to pass an absolute schema path and a symlink-escaped working path to the host CLI argument vector.

## T — one Docker invocation

- Probe ID: `issue3152-main-path-boundary-20260927-02`.
- Source commit: `fc4159ddd0b546c2adfe58faf8d40771e6e5dfc3`.
- Broker source Git blob: `5734f54f318db9ac5e96b2bed6f6bed105ac39ff`.
- Exact existing test source Git blob: `79405a089708a3f2d7c0982192592041125cf0dd`.
- Image: `ghcr.io/zaproxy/zaproxy:stable`, Linux/amd64 image ID `sha256:8d387b1a63e3425beef4846e39719f5af2a787753af2d8b6558c6257d7a577a2`, Python 3.11.2.
- Materialize exact GitHub-readback source bytes in a 16 MiB private tmpfs only after Git-blob checks. Load the existing test module directly (not `unittest discover`, which requires a package marker absent from the source tree).
- Run the entire current-main broker test module. Then call the actual broker `serve()` once using a synthetic request, with only `subprocess.run` mocked as a recorder. Request schema `/etc/passwd`; make `/repo/link` symlink to a sibling temp directory outside the repo and use it as `working`; also independently resolve `/repo/../../etc/passwd`.
- Docker flags: one invocation; `--network none --read-only --cpus=2 --memory=2g --pids-limit=128 --cap-drop ALL --security-opt no-new-privileges`; private `/tmp` tmpfs only.
- No real Codex executable, model/provider call, GUI, image, user data, input, task effect, or formal #3152 allocation.

## D

- `PASS_PATH_CONFINEMENT_GAP_REPRODUCED` iff exact source blobs match, all existing unit tests pass, and the mock recorder receives an outside absolute schema plus a working path resolving through the repo symlink to outside the repo (the traversal control also resolves outside).
- `NO_GAP_REPRODUCED` iff exact source blobs match, all existing unit tests pass, and the broker rejects or confines these paths before the mock boundary.
- Otherwise `STOP_SOURCE_OR_HARNESS`.

This only probes a host-path prerequisite raised in #3152's existing handoff. It cannot satisfy or consume #3152's held-out, typed-versus-scalar live model-escalation comparison.

## C / U

Mocked argument construction is not a successful host file read, data disclosure, model response, or task outcome. This Linux mapping probe makes no claim about Windows path semantics or production exploitability. Evidence-role admission, observation cost, downstream reserve, and model/task outcome remain untested.
