# Issue #2849 — real OrbStack host-model preflight

**Disposition: `FAIL_RUNNER_EVENT_COUNT_CONTRACT`; six-task allocation not started.**

This is an executed model/transport experiment, not only a container unit-test
rerun. On 2026-09-21, the latest #3647 code (`6a942ea04bfea1d196d19719ec59a9bdad720826`)
sent one no-image `handle` request from an OrbStack Linux/arm64 container to
the host Codex CLI through the shared-volume IPC broker. The host CLI returned
exit 0 and emitted one completed turn with usage and one assistant JSON message
that independently validates against the frozen plain schema. The checked-in
container runner nevertheless exited 1: it counts every `item.completed`
event as a message, including a completed `type=error` warning item, so it
observed two completed items instead of one. It did not create
`process.json`; this is a runner contract failure, not a successful preflight.

The plan registered plain then compiled as one bounded sequence. Because the
plain attempt failed at the container runner gate, the predeclared stop rule
prevented the compiled attempt, any retry, and the six-task allocation.

## H/T/D/C/U

- **H:** The selected Docker preflight path can carry one no-image schema probe
  over OrbStack IPC and return exactly one completed assistant JSON message,
  one completed turn with usage, and a schema-valid object.
- **T:** Latest PR #3647 head `6a942ea04bfea1d196d19719ec59a9bdad720826`,
  based at selection on main `befe92124434406ee6881b50195b3f01871191df`.
  Plain then compiled schemas were preregistered; only the plain attempt ran.
- **D:** Container image
  `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
  OrbStack `orbstack`, Linux/arm64, `--network none`; source inputs read-only,
  empty temporary workspace; host Codex CLI `0.146.1`, Node `v26.7.0`;
  requested model `gpt-5.6-luna`, effort `low`. Host broker returned exit 0,
  recorded one invocation and `authority_granted=false`. The container client
  returned 1. A separate read-only, network-disabled audit container parsed
  the event stream and schema and reproduced the failure classification.
- **C:** The host CLI produced a valid endpoint response, but the selected
  container runner did not accept or receipt it. The runtime/schema-preflight
  gate therefore **fails**. No GUI, image, target, input authority, task
  effect, efficiency, or six-task acceptance was tested. One real request used
  12,284 input tokens and 90 output tokens; monetary cost is unavailable.
- **U:** Preserve as a runner failure. Do not infer success from the host
  response alone. The next distinct hypothesis is whether an additive runner
  that counts only completed `agent_message` items (while retaining and
  classifying auxiliary error items) can produce the required process receipt
  and pass the same frozen-schema gate. That requires a new preregistered
  successor experiment; no retry is included here.

## Exact observed boundary

The model stream contained:

```text
thread.started
turn.started
item.completed(item.type=error)       # skills-context-budget warning
item.completed(item.type=agent_message) # schema-valid JSON
turn.completed(usage present)
```

The independent audit passed all six *failure-reproduction* checks:
one non-authoritative no-image request; one successful host CLI invocation;
one completed turn with usage; exactly one assistant JSON message; valid plain
schema output; and a container exit 1 caused by the runner's all-item count.
The assistant JSON SHA-256 is
`da29117c3edd11a7506ebd847958781d01f40be9e5e3ccef333357912b23edcd`.
The actual IPC request, response stream, broker receipt, container stdout and
stderr, client receipts, independent audit output, and failed pre-model harness
setup are retained under `evidence/`.

The failure line is 67 in the frozen
[`container_host_model_ipc_runner_v1.py`](https://github.com/Unjuno/agent-interface/blob/6a942ea04bfea1d196d19719ec59a9bdad720826/research/live_control/container_host_model_ipc_runner_v1.py#L67):
it selects all `item.completed` rows; lines 68–69 reject a count other than
one. The existing test-only shared-volume transport result for #3311 used a
fake CLI and is not changed or relabeled by this real-model result.

## Reproduction and integrity

`run_preflight_experiment.py` records the one-shot backend/broker invocation;
`audit_failed_preflight.py` independently parses the raw event and schema in
an offline container. `PRE-REGISTRATION.md` and its setup-only addendum were
frozen before the model request. `SHA256SUMS` covers all retained report,
source, and evidence files other than itself.

Current main at PR preparation: `600dabef6bdc071214eb2fbad80411cc271fc0d5`.
This additive report is associated with Issue #2849 and does not modify PR
#3647's branch or change any prior allocation result.
