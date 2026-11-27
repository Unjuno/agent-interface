# Independently serviced owner cancellation relay

Repair the negative actual-Executor composition from#8997. Keep default backend
selection unchanged; add an explicit cancellation-capable service launch option.
Use a second private socket, independently serviced from ordinary request/reply.
Both paths decode through the same locked, bounded original-source Lease registry.
A cancel arriving first creates a cancelled lease; later down cannot undo it.
Wrong generation/source or control transport failure retires registry authority
and cancels every known lease. It cannot create replacement input authority.

Control readiness binds service/display/owner. Each request carries exact RPC-v2
source/deadline/intent fields with cancellation true and monotonically increasing
request ID. A response separates cancellation acceptance from a bounded wait for
the matching native owner cause. Parent validates cause intent/source/deadline,
state and verification before recording it on the original Lease instance.
Missing/unknown cause stays unverified; a late result cannot rewrite first receipt.
Parent watcher is explicit, finite-inventory and separate from the ordinary RPC.
No cancelled press is retried, and no real display/input or WSL/container is used.

Files: input_owner_cancel_v4.py (registry, control service/client); minimal hooks
in input_owner_rpc_v2.py and input_owner_process_v3.py; test_input_owner_cancel_v4.py
(inert invariants and real owned-process Fake X actual-Executor composition).
Preserve first red, fixed sources, raw startup/control/recovery/finish/edge bytes,
commands, source pins and cleanup. Run normal/-O selected regressions. Independent
saved audit plus altered-record negatives precede bounded review/integration.

Required cells: pending cancel before registration refuses down; changed source
and wrong generation refuse; actual Executor paused after down receives verified
release cause before worker resume; ordinary RPC in flight does not block control;
blocked Fake release returns unverified and retains custody; late settlement does
not upgrade that first receipt; control loss cancels known lease and retires future
authority. Parent shutdown joins watcher/control workers without PID-based kill.
Native release-time, production backend selection, controller/session death,
task effects and matched economics remain unqualified follow-on gates.
