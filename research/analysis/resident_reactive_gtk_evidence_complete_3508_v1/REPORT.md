# Resident-reactive GTK evidence complete — allocation 03

**Decision:** `PASS_SYNTHETIC_RESIDENT_GTK_EVIDENCE_COMPLETE` for this one synthetic GTK/X11 policy fixture only. This is not production-runtime validation.

## H/T/D/C/U

- **H:** A generation-bound resident policy can emit once on valid current rising edges, refuse stale/revoked/replayed events, and preserve task-success classification only when the GUI effect is actually observed; reduced controls expose unsafe witnesses.
- **T:** 9 cases × 4 policies = 36 rows in one OrbStack container invocation, no retry, pinned linux/arm64 image `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, Docker 29.4.0, `--network none`, private Xvfb :200. Main source reference at freeze: `7cda063936b89c3f0cd58c0ebd1b78497e0ad2b8`. Screenshots sampled after XSync and a frozen 50ms settle. Source/code/output hashes and exact runner/auditor are in the evidence bundle.
- **D:** The frozen independent auditor passed all 36 unique rows with zero errors. Candidate policy: four positive visible effects; zero emissions on revoked/stale, delayed-old, target-replacement, and restart/replay; effect-unavailable was `TRANSPORT_WITHOUT_EFFECT` and never task success. All expected before/after pixel deltas matched the effect state. All GTK children exited 0; all XTEST releases were verified; Xvfb exited 0 and was waited.
- **C:** Synthetic policy harness + local GTK window/X11 only. Restart/replay is a journal/reinitialization simulation. No production runtime, real user task, agent loop, quality, latency, cost, or broad desktop reliability claim.
- **U:** Whether this bounded policy behavior transfers to production event/control architecture and end-to-end agent benefit remains unknown.

## Outcomes

Class counts across all policies: `VERIFIED_TASK_EFFECT=13`, `SAFE_REFUSAL=6`, `CONTROL_UNSAFE_WITNESS=10`, `TRANSPORT_WITHOUT_EFFECT=4`, `NO_EFFECT_EXPECTED_POSITIVE=3`. A task succeeds iff its outcome class is exactly `VERIFIED_TASK_EFFECT`; safe no-op/refusal is never success.

Original raw JSONL SHA-256: `6058d2053f645e3a598cc199158a63628e86385c298514a0bb4bef84f708ce4b`. Cleanup receipt SHA-256: `04b32a57100590860dca2646dd0d9b9c5d586c7cbede00ad9be3e892990449f8`. The bundle losslessly stores the three unique raw X11 screen buffers by content hash and includes a reconstruction helper; it reconstructs and re-audits all 72 screenshot references.

The previous allocation #3506 remains HOLD due two screenshot-delta mismatches and is not modified. Allocation #3504 remains a pre-row STOP. Earlier #3488/#3499 evidence also remains unchanged.

See `evidence-3508.tar.gz` for the freeze, source, raw rows, cleanup receipt, compressed lossless screenshot captures, reconstruction helper and audit report.