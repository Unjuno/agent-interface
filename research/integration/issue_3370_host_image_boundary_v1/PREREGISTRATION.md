# Issue #3370 — single direct-host-image task unit

## H/T/D/C/U

**H — hypothesis.** In one fresh managed Inkscape allocation, an observation
returned as a native MCP `ImageContent` block can be forwarded unchanged into
the current Codex model context; the same model can use that image plus the
public task to author one grounded action that produces the independently
scored saved effect with verified input release.

**T — one bounded unit.** Freeze current main `71c712eb6dd11dc3cc167fd7a0588a85c89822ce`,
the native MCP adapter/harness, OrbStack image
`sha256:97e1fc48a5ec95cc45aa993f43ac74b6c0ce982e035536ec27decdcc0f78cc14`
(`linux/arm64`), seed `991120`, and this runner/auditor before starting. Run one fresh Inkscape task in a private
network-disabled container with read-only source, persistent MCP stdio session,
and a dedicated writable evidence mount. Forward the returned image block
directly to this model as an image item (no image-file/viewer step before the
decision), together with only the returned public goal/context. The model then
authors one source-sequence-bound action, submitted once with `finish_after`.
Permit only same-request `native_resume` if the returned response is pending;
never resubmit or replay input. Independently audit the exact saved SVG effect,
source/request/reply/image identity, one decision/one submit accounting,
release, cleanup and process exit. No provider API calls or additional task.

**D — disposition.** `PASS_DIRECT_HOST_IMAGE_SINGLE_TASK_SCOPED` requires the
returned image to be the exact MCP image bytes, one explicit decision bound to
that source sequence, one submit (zero resubmits), independent task success,
verified empty release, complete raw lineage and independent audit PASS.
Setup/instrumentation failure is STOP; missing image/lineage or unverified
effect/release is HOLD/FAIL as specified in `audit.py`.

**C — controls.** Same fixed assistant/model across image receipt and action;
fresh unique allocation; image and source identities are hashed; no host desktop,
external app or network access; guarded one-shot decision and independent SVG
oracle. Container path and immutable source identity remain explicit.

**U — unresolved.** This tests direct image visibility/use for one task only. It
does not timestamp host presentation or model interpretation, compare against
the saved-file/view-tool route, exercise no-image/delayed/stale/disconnect
controls, expose provider token/cost usage, or establish latency benefit. The
parent #3370 remains open for its full boundary gate.

## Formal lineage / STOP record

`formal-01` was a consumed allocation and stopped before producing an image:
the container lacked `wmctrl`, required by `PrivateSession.windows()`. Its raw
MCP response, launch logs and cleanup record are preserved under
`evidence/formal-01/`; it is not a task trial and is not retried.
The source recipe was amended additively to install `wmctrl`. The corrected
OrbStack build has digest
`sha256:cf02676f620c6679614a311c4baee4deceb135a37cae9d6e14c39a5e8e49001e`
(`linux/arm64`). Its formal allocation receives a new identity, `formal-02`.

`formal-02` reached the image handoff but its attached stdin closed at the tool
boundary before the one decision could be returned; its cleanup and `STOP` are
preserved. No action was submitted. For `formal-03`, the frozen client uses a
dedicated `model-decision.json` file on the evidence mount as its one-shot input
handoff and times out after five minutes. The host wrapper emits the exact MCP
image bytes as a model image item directly, without a viewer transformation.
This corrected input route is fixed before the new allocation is launched.
