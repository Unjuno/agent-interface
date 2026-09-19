# Clock-domain recovery successor preflight (#2228)

This records the bounded container contract for the live/model-facing successor to #950. It preserves the synthetic controls but reports no live clock-domain or model result.

## H/T/D/C/U

- H: temporal ordering is not semantic causation; retry needs idempotency and generation evidence.
- T: distinguish same-clock, cross-clock apparent pre-actuation, delayed post-release, wrong target, unknown clock, no effect, and unauthenticated effect cases.
- D: `work/clock-domain-recovery-preflight.py` enumerates seven controls and conservative dispositions.
- C: no private application/input fixture, cross-process clock harness, independent scorer with clock metadata, or connected model/policy was available.
- U: live clock transfer, held-out route, model recovery, and independent scoring remain unverified.

## Stop

`STOP_LIVE_CLOCK_DOMAIN_MODEL_RECOVERY_NOT_EXECUTED` — synthetic timestamp agreement must not be promoted to live cross-domain recovery.
