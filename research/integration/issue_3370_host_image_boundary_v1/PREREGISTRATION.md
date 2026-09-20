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
