# Issue #59 — v13 scorer composition OrbStack A01

Decision: `PASS_CONSTRUCTION_SCOPED`.

## H / T / D / C / U

- **H:** current-main MAP01 v13 scorer-only composition passes the retained synthetic episode/thread/provenance contract in the pinned OrbStack container.
- **T:** one candidate invocation ran `research/doom/test_session_map01_v13.py` under the explicit Python entrypoint, with network disabled and the repository mounted read-only. No real game, X11 session, input, or model call occurred.
- **D:** 4/4 construction assertions passed. The raw-only auditor independently confirmed the freeze/source hashes, raw result contract and invocation cardinality with zero errors.
- **C:** the fake game/pipe schedule may fail to cover behavior of a real VizDoom episode or X11 owner.
- **U:** this is synthetic composition evidence only. It does not establish real release telemetry, scorer timing under gameplay, independently useful progress, model-wait recovery, threat control, or MAP01 completion.

## Execution record

- Base main: `9379817a8a5f5c3dda86be7db4d2ca226358854b`.
- Image: `linux/arm64`, `sha256:ebb7ae5e517a94516e0e22a2dec1013f95ce5432a23a03784e6621682ee8cf1c`.
- Candidate: 1 invocation, exit 0, 4 tests / 0.077 s, retries 0. Auditor: 1 separate invocation, exit 0, `PASS_CONSTRUCTION_SCOPED`, errors 0.
- Freeze SHA-256: `216a71c15c5eb6a642577d1f039f2c34aaee952dd6f52b7c22144c296b56192e`.
- Raw stdout SHA-256: `e6a0fc179d94d4d1693c7c490589a64abdbe7a9a20e62e844b92985833b69e42`.
- Obstac receipts and the raw/audit records are in this directory. The earlier command-shape STOP is preserved in `FREEZE.json`; it occurred before candidate invocation and is not pooled into A01.
- Existing MAP01 local CI construction/guard suites passed 31/31; exact commands and host Python version are in `LOCAL_CI.md`. They ran as repeatable checks and do not increase the one-shot candidate/auditor counts.

This does not consume, replace, or satisfy the separate R134 live allocation. It is a construction rung only; the Issue #59 real MAP01 telemetry/threat-control gate remains open.
