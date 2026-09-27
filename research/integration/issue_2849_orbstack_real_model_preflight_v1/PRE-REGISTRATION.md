# Issue #2849 one-shot host-model schema preflight — pre-registration

Frozen before model invocation on 2026-09-21 (Asia/Tokyo).

## H/T/D/C/U

- **H:** The latest #3647 selected Docker preflight backend can carry a single
  no-image schema-compatibility request from an OrbStack Linux/arm64 container
  over its shared-volume IPC runner to the host Codex CLI; the returned stream
  will contain exactly one completed assistant JSON message and one completed
  turn with usage, and the message will satisfy the requested schema.
- **T:** Latest #3647 head
  `6a942ea04bfea1d196d19719ec59a9bdad720826`, based on main
  `befe92124434406ee6881b50195b3f01871191df`. Execute one fresh `handle`,
  no-image request for the plain schema, then one for the compiled schema, in
  that order. Use OrbStack `orbstack`, Linux/arm64, Docker image
  `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
  and the checked-in #3311 host broker/container IPC runner at the frozen PR
  head. Host Codex CLI identity at freeze: `codex-cli 0.146.1`; Node
  `v26.7.0`.
- **D:** Keep the container on `--network none`; mount the runner, prompt,
  instructions, schema, and IPC as specified by the selected backend; use an
  empty per-attempt workspace and unique per-schema IPC/output directories.
  Host broker runs once per attempt with a 90-second timeout and
  `CODEX_EXE=/opt/homebrew/bin/codex`. No GUI, image, task target, input
  authority, or six-task allocation. Independently require: container exit 0;
  broker receipt says host CLI invoked and exit 0 with `authority_granted=false`;
  exactly one `item.completed` assistant message and one `turn.completed` with
  non-null usage; no `error`/`turn.failed`; JSON message parses and validates
  against the schema using the pinned offline validator; output says
  `authority_granted=false`. The two schemas are separate fresh attempts.
- **C:** A pass establishes only a real host Codex CLI/OrbStack IPC schema
  preflight for these two schemas on this machine and these pinned sources. It
  does not establish semantic quality, GUI/task effect, six-task execution,
  latency/cost benefit, or general runtime correctness. All model-generated
  output and raw event streams are retained. Do not expose credentials.
- **U:** If either attempt fails, times out, is malformed, lacks usage, fails
  schema validation, or cannot verify authority denial, stop at that exact
  stage, preserve it as STOP/FAIL, perform no retry and do not start the
  six-task allocation. If both pass, retain the bounded result and separately
  review the six-task allocation's freeze/authority requirements before any
  later allocation.

## Frozen inputs

- PR branch source commit: `6a942ea04bfea1d196d19719ec59a9bdad720826`.
- Current main at selection: `befe92124434406ee6881b50195b3f01871191df`.
- `docker_model_call_backend_v1.py` SHA-256:
  `da16f6f9a47125e3a8fe5259c2271c53f9dab9d54b5020c7f62e4f28ddabe17b`.
- `container_host_model_ipc_runner_v1.py` SHA-256:
  `091fbe29e2ecfb7eba1d77c124d22c67b3d2487950fd52b5b8307e397dc835b2`.
- `host_model_ipc_broker_v1.py` SHA-256:
  `0f6a812effe4807bf2997fba62bbabe8ea26288fcb644d7951b7c5cb24f4be57`.
- `docker_schema_preflight_v1.py` SHA-256:
  `b817ca5f2a407d89bd3b6c8b385248152e82955307dcb69f782b034da272fff4`.
- `schema_preflight_responder_v1.txt` SHA-256:
  `fd2785852cd55d2a742fba02f3f214839c912a016e9782339e1eb888d2cfb4ef`.
- Plain schema SHA-256:
  `0631ab7b7ba0aaf77a4cbdf758a8dbfba557dfb5120a9d5aa789223c97944291`.
- Compiled schema SHA-256:
  `a1a5901b84656375657538d2dccb975e3b40a5b22272abbab487c54904db1d0f`.

The preflight prompt is fixed by the selected source as: “Schema compatibility
probe. Produce any object accepted by the supplied schema.”
