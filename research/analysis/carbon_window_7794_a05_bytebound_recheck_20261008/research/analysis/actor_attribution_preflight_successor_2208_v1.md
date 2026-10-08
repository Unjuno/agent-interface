# Actor attribution successor preflight (#2208)

This is a container-only contract preflight for the live/model-facing successor to #1211. It preserves the synthetic controls, but records no live result.

## H/T/D/C/U

- H: exact actor lineage is a prerequisite, never proof of task success or permission for a new input.
- T: distinguish self, external, human/OS, same-session other-intent, conflicting, spoofed/unknown, and no-mutation cases.
- D: `work/actor-attribution-preflight.py` enumerates eight controls and fail-closed recovery dispositions.
- C: no private application fixture, real second-process/OS mutation harness, live model/policy, or independent effect/state scorer was connected.
- U: live transfer, held-out route, model recovery quality, and actor-provenance quality remain unverified.

## Stop

`STOP_ACTOR_ATTRIBUTION_LIVE_MODEL_NOT_EXECUTED` — do not report synthetic contract coverage as live actor attribution or model recovery.

The preflight output hash is `f5ad710d41e2b8f63b51b9c542c3542d1564928085d2fc6a4745ace7e63e1` only for the printed control payload; the live evidence set is empty.
