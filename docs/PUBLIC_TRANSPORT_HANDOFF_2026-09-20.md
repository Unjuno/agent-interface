# Public transport integration handoff — 2026-09-20

Implementation snapshot: main `0e5df8ae27dd9e2b9e20d84d3dff8c15a7710e9b`.
This supplements the [earlier integration snapshot](INTEGRATION_STATUS_2026-09-20.md).
It records usable integration surfaces and their limits, not a performance win
or a completed product. Frozen research results keep their original scope.

## Available entry points

| Entry point | Current behavior | Setup |
|---|---|---|
| Python API | Explicit one-shot dispatch and read-only observation; shared result presentation is available to callers | [Public API](../runtime/cli_v1/README.md) |
| CLI | The same APIs, with optional receipt and PNG review in one response | [Current interface](../runtime/USING_CURRENT_INTERFACE.md) |
| Public MCP | Fixed startup targets; one API call per tool; metadata and native image blocks; no research allocation required | [MCP setup and lifecycle](../runtime/cli_v1/MCP.md) |
| Portable archive | Committed-source CLI plus explicit optional `mcp` mode; MCP dependencies are needed only for that mode | [Build and launch](../runtime/distribution_v2/README.md) |

These are choices for the caller. There is no automatic transport router and no
measured claim that MCP, CLI or direct API is cheapest. The public MCP adapter is
distinct from the research harness's managed native MCP allocation. It does not
launch an application, issue source authority or manage a general desktop session.

## Changes since the earlier snapshot

| Integration | Caller-visible change | Reference |
|---|---|---|
| Bounded key repetition | One repeated key instruction expands into an ordered bounded program; original source mapping is retained | [#3527](https://github.com/Unjuno/agent-interface/pull/3527) |
| Failure position | Review can identify the original instruction and repeat occurrence, preserving partial-effect uncertainty | [#3535](https://github.com/Unjuno/agent-interface/pull/3535) |
| Optional public MCP | One-shot APIs are available over stdio without a second model; overlapping calls return busy rather than queueing input | [#3538](https://github.com/Unjuno/agent-interface/pull/3538) |
| Explicit X11 display | Explicit display selection works without inheriting DISPLAY and does not mutate process environment | [#3542](https://github.com/Unjuno/agent-interface/pull/3542) |
| Shared review fallback | CLI/MCP retain the same raw action result and outcome summary if presentation raises | [#3546](https://github.com/Unjuno/agent-interface/pull/3546) |
| Portable MCP mode | The archive launches outside a checkout; ordinary CLI operation does not require the MCP SDK | [#3552](https://github.com/Unjuno/agent-interface/pull/3552) |
| Initialization failure receipts | Unexpected construction errors return structured failure information instead of escaping as a traceback | [#3556](https://github.com/Unjuno/agent-interface/pull/3556) |

MCP cancellation does not prove input stopped: the existing worker can finish and
retain its result. An uncertain action is not automatically replayed. Current
source/binding/lease values remain caller supplied. One-shot session behavior must
not be generalized to safe recovery after a host or target lifecycle change.

## Primary use and verification boundaries

[Draft #3532](https://github.com/Unjuno/agent-interface/pull/3532) retains portable
CLI use: type ABCDEF, move Left three times, insert a hyphen and save. Independent
readback and a later explicit observation confirmed ABC-DEF. The action capture
itself was stale. Its post-run source review identifies synchronous event logging
on the Windows-mounted /mnt/c directory as an uncontrolled possible delay, not a
proven cause or a measurement of ordinary application responsiveness.

[Draft #3549](https://github.com/Unjuno/agent-interface/pull/3549) retains one
public MCP stdio connection: the primary agent viewed the initial image and chose
one input/save program. Application readback confirmed mcp-save-3546, while the
returned image remained stale. This was SDK-mediated primary use, not a tool
registered directly in the conversation. There was no second model or input replay.

The draft records remain unmerged pending their evidence gates. They do not
establish end-to-end useful-feedback latency, semantic completion time, token
savings or a transport comparison. Local dispatch intervals exclude model/image
presentation and must not be presented as those metrics.

The #3552 implementation passed 182 WSL integration tests and six Windows
distribution tests. The subsequent #3556 change passed 33 relevant WSL API,
observation and MCP tests plus a read-only invalid-display check. These counts
refer to their respective checked revisions, not a new full-main performance audit.

## Next decisions

- [#3544](https://github.com/Unjuno/agent-interface/issues/3544) defines the
  MCP/API/CLI comparison and possible router: same model/task/environment,
  equivalent visible information, actual usage/cost where available, cold/warm
  separation, correctness, useful feedback and recovery cost. Include router
  overhead; prefer a fixed route if conditional benefit is not established.
- Continue integrating independently validated research. Sensor design and
  experiments remain with the separate research work; this stream does not
  develop sensors. A research gate marked HOLD is not a production adoption.
- Host registration, lifecycle recovery, useful feedback, model cost and broader
  desktop/game coverage remain open. Building the portable file does not publish
  a GitHub Release or establish release readiness.
