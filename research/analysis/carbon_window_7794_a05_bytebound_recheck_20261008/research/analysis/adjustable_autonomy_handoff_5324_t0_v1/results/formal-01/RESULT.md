# T0 result — adjustable-autonomy responsibility handoff (#5324)

Disposition under the frozen decision rule: **`PASS_HANDOFF_BOUNDARIES_SCOPED`**.

One formal invocation ran 5 policies × 13 fixed event schedules (65 cells) on Windows 11 x86_64 with CPython 3.12.10, standard library only. The simulator and independent raw-only auditor were each invoked once. Runner exit 0; auditor exit 0, 65 traces, `errors=[]`. No Docker, model, GPU, GUI, external actor, or task input was used. All durations are logical event ticks.

## Aggregated result

| Policy | No-owner ticks | Duplicate-owner ticks | Work events with no owner | False task-success claims |
|---|---:|---:|---:|---:|
| `ROUTE_ONLY` | 74 | 1 | 0 | 0 |
| `ACK_ONLY` | 12 | 12 | 0 | 0 |
| `TWO_PHASE` | 26 | 0 | 0 | 0 |
| `THREE_PHASE` | 26 | 0 | 0 | 0 |
| `FAIL_CLOSED_NO_OWNER` | 82 | 0 | 1 | 0 |

The two-/three-phase policies meet the frozen invariants: zero duplicate-owner ticks and zero false success claims. Both improve the selected nominal/lost-offer/reclaim no-owner-gap comparator against always-stop, and retain the one scheduled nominal work event that `FAIL_CLOSED_NO_OWNER` cannot perform.

## Interpretation and limitation

This is not a single-policy win. `ACK_ONLY` has fewer aggregate no-owner ticks (12 vs 26) but incurs 12 duplicate-owner ticks. Two-/three-phase remove that overlap but spend more ticks without an owner while transfer commits or recovery proceeds. Versus `ROUTE_ONLY`, the two-/three-phase policies reduce both measured problems in this finite matrix (74→26 gap ticks; 1→0 duplicate ticks). The outcome therefore supports a scoped safety/liveness tradeoff under these specific protocol definitions; it does not establish that explicit handoff universally reduces both gap and duplication, or which policy is preferable under real-time costs.

In particular, after the source crashes following target acceptance but before a quiescence receipt, the two-/three-phase protocols leave a modeled gap instead of activating the target on acknowledgement alone. Human takeover prevents later two-/three-phase activation in the frozen human-intervention schedule. These are protocol-model observations only, not evidence that any real source, target, broker, or human obeys the protocol.

## Provenance

- Frozen main: `e05cefde72a418e8574efddeae082de3490e5cd8`
- Allocation: `adjustable-autonomy-handoff-5324-t0-e05cefde-20260930-01`
- Raw traces: `raw.json`, 284,829 bytes, SHA-256 `23cebc74baec7ac025a56bb6a2bc3b332ca9d8abf865758f1f9813627d2eedc9`
- Independent audit summary: [`AUDIT_SUMMARY.json`](AUDIT_SUMMARY.json), audit source SHA-256 from freeze `ce07fbef3e3b75fe24060df49ce2b0ee2e5ca48a5d05d9929e2cc791ef2c6211`
- Freeze and exact commands: [`../../FREEZE.json`](../../FREEZE.json), [`../../FREEZE_COMMENT.md`](../../FREEZE_COMMENT.md)
- Construction suite: 7/7 passed before the one-shot run.

## Scope boundary

The tested policies are operational definitions in this research package, not current runtime implementations. There is no wall-clock/handoff latency, user-burden, GUI effect, lease-authority, release, human-attention, or production-runtime measurement. #5320's session-typed lifecycle experiment is a separate predecessor; its matrix was not replayed or pooled here. This result does not authorize T1 or any runtime/product claim.
