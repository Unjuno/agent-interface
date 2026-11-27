# Issue #1998 T0 A02 — focused payload size vs full-frame

## Delta from the retained predecessor

The current-main #1935/#1998 package already tests 256 request-validation cases, freshness/identity/bounds refusal, and exact crop reconstruction. It excludes token/latency savings and does not compare serialized focused payload size with a full-frame payload. A02 measures only that missing byte-accounting discriminator on a larger deterministic image fixture.

## Hypothesis

For a unique, current, in-bounds focused region, the exact crop payload plus all required metadata is smaller than the canonical full-frame payload for at least one preregistered ROI size; the byte difference is zero-risk to crop identity and exact source pixels. If metadata makes every focused payload no smaller, record `HOLD_NO_SIZE_GAIN`. A large valid ROI may be larger than full-frame and must fall back to the full-frame representation.

## Frozen design

One 64×64 grayscale 8-bit deterministic frame is paired with nine valid ROI sizes (8, 16, 24, 32, 48, 56, 62, 63, and 64 square) and five invalid requests (stale epoch, replaced frame identity, lost focus, ambiguous region, and out-of-bounds region). Both `FULL_FRAME` and `DECLARED_FOCUS` payloads use canonical JSON with base64 pixels and all declared identity/epoch/geometry metadata. Count UTF-8 serialized bytes including metadata. Independently reconstruct every selected pixel from the frozen binary source.

A valid focus payload is selected only when its full serialized size is strictly less than full-frame. Otherwise select FULL_FRAME with `FULL_FRAME_NO_SIZE_GAIN`. Invalid requests produce no focused payload and select the exact full frame. This is packaging classification only; it grants no action authority.

## Decision gate

`PASS_FOCUSED_PAYLOAD_REDUCTION_SCOPED` iff the independent auditor reconstructs all 14 cases and all exact pixel bytes, rejects all 6 mutations, admits only the 9 current unique in-bounds requests, abstains on all five planted invalid conditions, chooses focus only when bytes are strictly smaller, and records at least one positive byte saving. `HOLD_NO_SIZE_GAIN` if there is no positive saving. Any stale/ambiguous crop, wrong bytes, or focus selection without strict size benefit is `FAIL_METHOD`.

## Execution boundary

Pre-freeze construction tests write no formal output. After freeze and Issue allocation record: candidate once, then independent raw-only auditor once only on candidate exit 0; retries 0. Use an immutable frame fixture, standard-library Python, isolated outputs, no model, GUI, user data, network call, runtime action, or input dispatch. Prefer a pinned container if a healthy compatible engine/image is available; otherwise record the preflight and use macOS `sandbox-exec` network denial. Do not claim container evidence for host execution.

## Limits

This measures canonical serialized bytes for one authored frame, not model tokens, transport compression, real observation cost, model usefulness, visual accuracy, latency, GUI correctness, or product benefit. The crop coordinates and intended region are fixture inputs, not model-generated detections.
