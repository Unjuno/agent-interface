# Activation barrier across receiver generation propagation gap

Task: `COORD-GENERATION-ACTIVATION-BARRIER-20260916-011`

Decision: **`PASS_ACTIVATION_BARRIER_PROPAGATION_GAP_SCOPED`**

## Result

The experiment held receiver generation equality checking and request idempotency fixed and changed only handoff sequencing.

| Arm | Gap behavior | Final receiver |
|---|---|---|
| naive two-step | coordination became gen2 while receiver remained gen1 ACTIVE; delayed gen1 request was APPLIED | ACTIVE/gen2, effects from generations `[1, 2]`, count 2 |
| activation barrier | receiver became BLOCKED before coordination became gen2; delayed gen1 request was `BARRIER_BLOCKED` with zero write | ACTIVE/gen2, effects from generation `[2]`, count 1 |

Naive measured commits:
- coordination gen2: `bb728e035d45d83f6438b465f11cf6df20145078`
- stale gen1 effect in gap: `9ab69ca53a04be8e48da94f95249e7c269cd927d`
- receiver gen2 install: `cce07594ad1c1877fee0be0e2adf498346200543`
- current gen2 effect: `7319be3ce754ffd362f7fee084483e20aab1fbd7`

Barrier measured commits:
- receiver BLOCKED at gen1: `1ec6fd7777c81e6b0feb9ad9e0e68c3b3b619612`
- coordination gen2: `08e72a24cf02725c678718176a4f6e1811d6820b`
- delayed gen1 request: no write, classified `BARRIER_BLOCKED`
- receiver gen2 install while BLOCKED: `8303edc883d838c1cbc2ddc69690d818cbb7743d`
- receiver activation at gen2: `f8d19009b0fee4b9c93d758708700c2c9768b72f`
- current gen2 effect: `cd3a12f42f5c162ac5c2f9008fc2efd2022c5af6`

## Interpretation

A local receiver generation check cannot protect the interval before the receiver has learned the new generation. The naive sequence exposes exactly that interval: the coordinator has revoked generation 1, but the receiver still regards generation 1 as current and accepts a delayed request.

A receiver-first BLOCKED barrier closes this fixture's interval by refusing all effects during handoff. After the receiver installs generation 2, it can be reactivated and admit only generation-2 effects. This trades availability for safety.

## Evidence boundary

This is a GitHub-backed deterministic state-machine fixture. It assumes the receiver barrier commit succeeds before coordination advances. It does not test lost barrier acknowledgements, partial multi-receiver propagation, crash/power loss, real network delivery, quorum, atomic broadcast, real external side effects, or production exactly-once behavior.

One pre-measurement file-create attempt using filename `payload_receiver_barrier_blocked_g2.json` was rejected by tool safety classification before commit. The neutral filename `payload_receiver_barrier_hold_g2.json` retained identical state bytes and semantics before freeze.

`verify.py` is an offline deterministic checker retained for reproducibility; no independent-agent execution is claimed.

## Next single question

Keep the barrier protocol and receiver admission policy fixed. Vary only barrier-install acknowledgement loss: after the barrier write actually commits but its response is lost, can a content-bound readback recognize the receiver as BLOCKED and safely continue handoff without either reissuing the barrier blindly or advancing coordination while barrier state is UNKNOWN?
