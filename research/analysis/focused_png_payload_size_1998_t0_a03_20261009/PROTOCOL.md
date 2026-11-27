# Issue #1998 T0 A03 — canonical PNG crop payload accounting

## Distinct residual

A02 compared raw gray8 pixels serialized as base64 JSON. The observation-tiles path in current main uses PNG artifacts. A03 therefore isolates PNG chunk/deflate overhead and payload metadata without changing or rerunning A02.

## Frozen question

For deterministic synthetic RGB8 frames and fixed rectangular requests, does a lossless PNG crop plus all request metadata produce a smaller canonical JSON payload than the full-frame PNG for any valid ROI, while exact pixel reconstruction and fail-closed validation remain intact? The selector chooses a focused payload only when its complete UTF-8 JSON representation is strictly smaller; otherwise it selects FULL_FRAME.

## Fixture and accounting

Three 128x96 RGB8 frames are frozen: flat/UI-like structure, structured high-contrast edges, and deterministic seeded high entropy. Each receives six valid rectangles: 16x16, 32x24, 64x48, 120x88, full-frame, and 8x96. Five invalid controls cover stale epoch, replaced frame identity, lost focus, ambiguous region, and out-of-bounds. Total: 23 cases.

Canonical PNG uses RGB8, non-interlaced, filter type 0 per row, one zlib level-6 IDAT chunk, standard IHDR/IDAT/IEND chunk framing and CRCs. The serialized JSON includes base64 PNG bytes plus frame identity, epoch, geometry, media type, and region/reason metadata. The independent auditor validates PNG signature, chunk order/length/CRC, deflate termination, filter bytes, dimensions, exact source pixels, canonical JSON byte counts, selection and refusal behavior.

## Decision

`PASS_METHOD_SCOPED` only if the independent audit reconstructs all 23 rows and exact pixels, rejects all 6 frozen mutations, invalid requests emit no crop, every focused selection is strictly smaller than FULL_FRAME including metadata, at least one valid crop saves bytes, and at least one no-gain/full-frame case falls back. Any mismatch is `FAIL_METHOD`; no favorable rerun.

## Run boundary and limits

Construction tests precede freeze. After the freeze is committed and read back, candidate runs once and auditor runs once only if candidate exits 0 with bytes; retries are zero. The task-host is macOS. Attempt read-only OrbStack context/image inventory before formal execution; if container storage is unavailable, record the stop and use a `sandbox-exec` network-denied CPython standard-library run. Host execution is not container evidence. No GUI, user data, model, network, runtime action, or input dispatch.

This is synthetic canonical PNG byte accounting only. It measures neither Pillow timing nor a live capture/serialization pipeline, model tokens, transport compression, visual localization, GUI correctness, task success, or product benefit.
