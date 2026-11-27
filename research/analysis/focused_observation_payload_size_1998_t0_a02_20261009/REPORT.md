# Issue #1998 A02 — focused payload byte comparison

**Result: `PASS_METHOD_SCOPED`; subhypothesis: `SUPPORT_FOR_FOCUSED_PAYLOAD_REDUCTION_SCOPED`.** The frozen candidate and independent raw-only auditor each ran once under network denial (exit 0, retries 0). The auditor reconstructed all 14 cases and rejected all 6 mutations.

For the deterministic 64×64 grayscale frame, the canonical FULL_FRAME payload was 5,635 bytes per case including JSON metadata and base64 pixels. Eight of nine valid unique focused requests produced a smaller exact crop payload; the full-frame-sized ROI did not, so the selector retained FULL_FRAME. All five invalid requests (stale epoch, replaced frame identity, lost focus, ambiguous region, and out-of-bounds) emitted no focused payload and selected the exact full frame.

Across the 14 authored cases, full-frame representation totaled 78,890 bytes; selected representations totaled 55,957 bytes, a reduction of 22,933 bytes. The maximum per-case reduction was 5,313 bytes. These are serialized-byte counts for this fixture, not token, transport, latency, GUI, or task-success measurements.

## Method and environment

The existing main package `focused_observation_request_successor_1935_v1` already covers 256 request-validation combinations and exact crop reconstruction, but it does not compare serialized size against FULL_FRAME. A02 adds that bounded byte-accounting contrast using one frozen 4,096-byte source frame, nine ROI sizes, and five fail-closed controls.

OrbStack and Docker default context image inventories failed before listing images because containerd blob reads returned `operation not supported`. No container was started. The finite CPU method ran on macOS Darwin 27.0 arm64 with CPython 3.14.5 under `sandbox-exec` network denial, using only the standard library. Pre-freeze construction tests passed 4/4 normally and 4/4 under `-O`.

## Scope boundary

This supports only the synthetic serialized-byte subhypothesis. It does not show model-token or latency savings, visual detection quality, model usefulness, real GUI correctness, authority, or product benefit. The ROI and requested identity are fixture inputs, not model-generated observations. No GUI, model, user data, runtime action, or effect was used.
