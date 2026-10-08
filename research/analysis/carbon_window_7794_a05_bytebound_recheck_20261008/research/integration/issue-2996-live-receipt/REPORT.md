# Issue #2996 live observation → golden-v3 receipt composition

Task: `GOLDEN-LIVE-2996-20260920-01`  
Image: `agent-interface-2558-orbstack:20260920@sha256:1a16aa431254514de58c909e84e5094a8e894caac11bf4c9d937dde6ea6d6398`  
Network: `none`  
Canonical composer path: `research/integration/golden_v3_receipt_composition_2916/receipt_composition.py`  
Canonical composer SHA-256: `2450a4fa2881897265e9716236349be719c4b9854a3c523ed1936a2ae938ab4e`

## H / T / D / C / U

- H: a live exact X11 observation can be transformed into authority-neutral golden-v3 receipts while preserving session, target, sequence, and binding context.
- T: fresh Xvfb `:99` and live Tk window; derive the window identity and artifact digest; compose matching, stale-sequence, and authority-contradiction variants.
- D: `PASS_GOLDEN_V3_LIVE_RECEIPT_COMPOSITION_SCOPED` requires matching acceptance, deterministic refusal controls, `authority_granted=false`, and zero input/model/task-effect counters.
- C: one private X11/Tk topology, one observation, no input, no model/provider, no lease renewal, no application effect. This does not test target discovery, guarded input, or task success.
- U: identity sufficiency is established only for this fixture and source context.

## Result

`PASS_GOLDEN_V3_LIVE_RECEIPT_COMPOSITION_SCOPED`.

- Live target: X11/Tk window ID `2097155`; session ID was fresh for the allocation.
- Artifact SHA-256: `570a417724c7739811f806ba78b2c74e1cc307282e5abc9fcb334e7a33a42105`.
- Matching live observation: `ACCEPT_FOR_ORDINARY_ADMISSION`, `authority_granted=false`.
- Stale observation sequence: `REFUSE` with `ADMISSION_STALE_OBSERVATION_SEQ`.
- Contradictory dispatch authority: `REFUSE` with `AUTHORITY_CONTRADICTION`.
- Counters: input operations `0`, model calls `0`, task effect `0`.

The result is a provenance-composition boundary only. The receipt is not an application-effect claim and does not authorize input.

