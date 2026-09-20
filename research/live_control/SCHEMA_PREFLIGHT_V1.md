# Output-schema endpoint preflight v1

## Result

The first preregistered no-GUI block retains `schema_preflight_v1.py` as an
input-authority prerequisite candidate. It sends the proposed output schema
through the same Codex CLI response-format path used by
`target_handle_model_runner_v2.py`, before any application, screenshot or input
session is acquired.

Five fresh endpoint requests and one cache reuse were fixed in advance. The two
schemas retained from failed Mindustry allocations were refused:

- candidate `oneOf`: `oneOf is not permitted`;
- a property without an explicit type: the endpoint reported the missing
  `type` requirement.

Neither refusal completed a model turn or reported usage. Three schemas used by
the corrected path completed successfully. Their combined reported usage was
23,674 input tokens, 240 output tokens and 81 reasoning output tokens. Reusing
the identical compatibility key performed no new endpoint call and reported no
fresh usage.

## Cache identity

The compatibility key covers the schema, requested model and effort, runner and
instruction hashes, CLI entry hash, CLI and Node versions, and the exact
handle/no-image/output-schema request shape. The audit also verifies that
changing the schema, CLI identity or model changes the key. The endpoint's own
server revision is not independently exposed, so the cache proves compatibility
only for the recorded client/model identity and must not be treated as permanent
server compatibility.

## Explicit model-call backend routing

The integrated-efficiency runner performs fresh no-image schema preflights
before its task-specific grounding calls. Both phases must use the selected
backend; routing only `integrated_efficiency_model_v1.call` would otherwise mix
legacy WSL preflights with Docker-host-IPC task calls.

The legacy WSL path remains the default. To select the Docker module for both
phases, set these variables before starting the Python runner:

```text
AGENT_INTERFACE_MODEL_BACKEND=module
AGENT_INTERFACE_MODEL_CALL_MODULE=docker_model_call_backend_v1
AGENT_INTERFACE_DOCKER_RUNNER=<container-side IPC runner>
AGENT_INTERFACE_DOCKER_IMAGE=<pinned container image>
AGENT_INTERFACE_DOCKER_IPC=<host-model IPC directory>
AGENT_INTERFACE_DOCKER_SCHEMA_PLAIN=<plain contract schema>
AGENT_INTERFACE_DOCKER_SCHEMA_COMPILED=<compiled contract schema>
AGENT_INTERFACE_DOCKER_INSTRUCTIONS_PLAIN=<plain contract instructions>
AGENT_INTERFACE_DOCKER_INSTRUCTIONS_COMPILED=<compiled contract instructions>
```

The selected module must implement `call`, `preflight_call`, and
`preflight_identity`. Missing operations stop at import/configuration time; they
do not fall back to WSL. The Docker preflight uses the existing `handle` mode,
no image, network-disabled container and shared-volume host-model IPC. Its
cache identity includes the schema, runner and instructions hashes, model/effort,
request shape, IPC boundary and configured image reference, so a different
backend image cannot reuse the legacy WSL compatibility entry.
Task calls resolve schema and instructions by contract (`PLAIN` or `COMPILED`)
before validation and container mounting. The older unsuffixed schema and
instructions variables remain fallback aliases for single-contract callers;
multi-contract allocations should configure both suffixed pairs explicitly.

The backend selector is resolved when modules import; changing environment
variables later in the running process has no effect. Unit tests use synthetic
event receipts and command mocks only. They prove backend selection, identity
separation and failure handling, not Docker Desktop availability, endpoint
compatibility on the selected host, or six-task acceptance. The six-task
allocation remains a fresh containerized experiment and must be run only after
the runtime preflight is healthy.

## Scope

Windows and WSL audits both pass. They reconstruct every fresh request and usage
total, validate the successful outputs against their original JSON Schemas,
match the two refusal messages, verify five cache records and prove that the
reuse case has no model-call directory. The block contains no screenshots or
GUI artifacts.

This result does not establish semantic task quality, latency improvement,
token saving, endpoint-version completeness or human-tempo operation. The first
compatible checks consume substantial model input. Cache reuse removes only a
repeated compatibility request under an identical recorded identity.

## Decision and next allocation

Retain the preflight implementation and its cache. Issue #54 remains open until
a new live runner invokes this gate before acquiring input authority. That
runner should be evaluated in the planned finite matched Mindustry block with a
positive placement, a no-match abstention and an ambiguous-evidence abstention.
The historical v1-v5 runners and their failures remain unchanged.

## Follow-up authority gate

`schema_preflight_gate_v1.py` now requires every named schema to report
`ENDPOINT_COMPATIBLE` before returning to its caller. A second preregistered
no-GUI block covers the previously missing world-receipt `oneOf`: the endpoint
refuses it in 3,625.993ms with no completed turn or usage. The three production
schemas then pass entirely from copied, hash-pinned cache with zero fresh calls.
Windows and WSL audits pass.

`run_mindustry_single_tile_live_v6.py` places the complete gate before the
historical v5 continuation. A deterministic WSL test uses the actual six-entry
cache: an incompatible schema invokes the continuation zero times, while the
three compatible production schemas invoke it once with zero endpoint calls.
This proves caller ordering. The v6 path has not yet run the application, so it
does not establish live task correctness or latency.

Primary artifacts:

- `results/schema-preflight-01/preregistration.json`
- `results/schema-preflight-01/report.json`
- `results/schema-preflight-01/audit.json`
- `schema_preflight_v1.py`
- `run_schema_preflight_block_v1.py`
- `audit_schema_preflight_block_v1.py`
- `results/schema-preflight-gate-01/audit.json`
- `schema_preflight_gate_v1.py`
