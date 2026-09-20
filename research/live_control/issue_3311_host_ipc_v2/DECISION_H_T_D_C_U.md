# #3311 allocation successor decision

## H — hypothesis

The current main branch's explicit Docker model backend plus existing v1 host IPC broker can support the preregistered integrated-efficiency path, including current schema preflight, without adding a new transport protocol. Benefit and task outcome remain unknown. The experimental v2 broker is not selected: its fake OrbStack round trip did not complete and its temporary code/path mapping was not a sound basis for model calls.

## T — bounded test

First complete a no-model engineering gate: use the OrbStack-derived Linux/arm64 image pinned in `TRANSPORT_DIAGNOSTIC.md`; verify all GUI/test dependencies and the existing `runtime/host_model_ipc_broker_v1.py` path mapping; exercise request/response using a fake CLI only; run all adapter and frozen-protocol tests. Do not invoke model or GUI/task input until the adapter and preflight use the same frozen Docker/host-IPC boundary, every source/image/CLI identity is recorded, and the isolated gate passes.

Only then, and only if the issue remains current without conflicting work, freeze a separate `integrated-efficiency-live-02` allocation with a fresh seed and full H/T/D/C/U manifest. Execute its original six-task three-arm schedule once, without retry. Retain raw host/container logs, IPC receipts, independent scorer receipts, image identity, source hashes and all stop/failure reasons. The earlier failed v2 transport probes remain setup-only and are not samples.

## D — outcomes

- `PASS_TRANSPORT_GATE_ONLY`: fake CLI round trip and isolated adapter checks pass; no model, task, or efficiency claim.
- `STOP_TRANSPORT_UNAVAILABLE`: path/IPC/runner mapping or isolation cannot be verified; preserve diagnostic and stop before model/task calls.
- `HOLD_ALLOCATION`: the integrated allocation executes but a required usage/effect/comparability/audit gate is unavailable.
- `RETAIN` / `REJECT`: only as defined by the existing #3311 preregistration and only after the full allocation plus independent audit.

## C — controls

Preserve the existing versioned v1 transport and its tests. Do not grant GUI/input authority to the host model broker; require `authority_granted=false`. Container networking remains disabled. Fake CLI output is transport evidence only. No retries after the one formal allocation begins; preserve partial traces and classify infrastructure failures separately from product outcomes.

## U — unresolved

Does current OrbStack volume mapping support a fully verified v1 request/response flow from the formal runner? Can the current schema preflight be routed through that same boundary without changing frozen task semantics? Are actual usage and independent task effects available for a comparable allocation? Any unanswered gate means stop/HOLD, not a positive result.
