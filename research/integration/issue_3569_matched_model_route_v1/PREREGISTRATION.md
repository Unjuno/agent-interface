# Issue #3569 matched model-visible route task — pre-call gate

## H/T/D/C/U

**H — hypothesis**
The current Codex model host can receive one equivalent visual task through
three separately exposed Agent Interface routes (public Python API, CLI, and
stdio MCP), allowing a one-task-per-route comparison without changing the
model, host, task, or visual evidence.

**T — staged test**
Stage 0 is a route/model-host availability gate. Before creating the nonce or
making any task/model call, verify that the same active model host can select
each of the three routes directly, that route-specific tool definitions and
image payloads are visible at the model boundary, and that the model/session
identity is unchanged. In parallel, perform only a network-disabled OrbStack
runtime construction preflight: verify imports and CLI/MCP help for the
current-main source using the locally cached route-test image. Do not call an
observation route, create a fixture, generate the nonce, or invoke a model.
Proceed to the separately frozen task only if both gates pass. Do not replace
the active model, host, or route with a shell-mediated/manual image-reading
path.

**D — decision**
`PASS_ROUTE_HOST_PREFLIGHT` requires all three direct route affordances,
same-host/model identity, and observable route-specific task/image evidence.
`STOP_MODEL_ROUTE_UNAVAILABLE` if any required affordance, identity proof, or
host-usage receipt is unavailable. Such a STOP consumes zero task calls and is
not a task-performance result. Container construction failures are separately
`STOP_CONTAINER_PREFLIGHT`; do not retry. No route winner, latency, cost, or
correctness claim follows from Stage 0.

**C — constraints**
Starting main: `12f838151cc210c277e585f5c2fc8b837dedc55c`. OrbStack Docker
Linux/arm64; cached route-test image is pinned by immutable image ID in the
container preflight record; runtime network disabled, read-only source and
rootfs, isolated tmpfs. No model/provider call, image task, nonce, GUI input,
authority grant, or network use. Prior #3548/#3557/#3561 evidence is not rerun
or pooled.

**U — unknown**
Whether this active Codex model host exposes the three transports as directly
callable, separately measurable model routes with host-verifiable usage
receipts. A local CLI shell wrapper or manually presented screenshot does not
resolve this unknown because it hides/substitutes the route interface at the
model boundary.

## Frozen stop rule

Stage 0 is the whole allocation unless every direct model-host condition above
is established before a task call. Preserve a route-unavailable STOP as the
result; no nonce/task execution, replacement host, or relabeling is allowed.
