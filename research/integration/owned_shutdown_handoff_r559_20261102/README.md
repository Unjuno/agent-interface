# Shutdown admission and startup custody: review of r556–r558

Scope: design review of draft PR #10139 head `1bdf2a5db42674d34986e7325f0e302818655e12`, with independent Astra consultation. No runtime, input or GUI experiment was performed for this note. Earlier artifacts remain authoritative for their own conditions and results.

## Evidence

* r556 observed a private fake-owner snapshot complete after shutdown returned UNKNOWN while startup was gated.
* r557 observed that checking a shutdown Event before return is insufficient: the check can return false, then shutdown sets it and returns, and the old caller resumes and sends a request. The prototype was discarded.
* r558 gated a different ordering: an already-started child, with the parent's RPC paused before pipe send. Close retired the child and returned UNKNOWN/no replay; after resumption the call raised. This did not establish what happens to requests accepted by X before retirement.

## Candidate obligations, not an implemented fix

1. A short admission/custody critical section must linearize closing, generation, and the creation of startup and operation obligations. Do not hold that section over process creation, IPC, platform I/O, or cleanup. A request trying to enter after closing is rejected.
2. An obligation admitted before closing may still be paused just before send; registering a ticket does not stop its later transmission. Completion, or an independently verified fence of sender and receiver, is required before treating its future effects as absent. Otherwise preserve UNKNOWN and custody.
3. Registering startup in the parent before spawn does not itself preserve custody if the spawning thread never returns or the parent dies. To cover those cases, investigate a supervisor established before input authority that owns actual child creation and remains responsible on parent disconnect; post-spawn PID notification alone has a creation-to-notification gap. This is a proposal, not proof that the existing cancellation supervisor supplies that role.
4. Process retirement is not proof of X server queue drainage, input release or task success. Recovery needs separate target/display fencing, release readback and task-effect evidence; retain UNKNOWN/replay denial where any is missing.

## Required distinguishing tests

Gate before spawn, after spawn before registration, before admission, immediately after admission, immediately before and during send; include permanent stalls, parent termination, cancellation/close races, cleanup errors and duplicate close. Observe RPC receipt, exact child retirement, surviving custodian and input/readback separately. Include controls where shutdown does not occur, and do not count fixture cleanup as system cleanup. Then exercise the public MCP route and a fresh isolated application task under separately recorded conditions. A bounded test timeout alone cannot prove all scheduling or parent-death behavior.

The user-authorized WSLc r186 trial in `work/vizdoom-effect-isolated-wslc-r186` measured fresh ViZDoom movement and event separation after **manual** display replacement. It is one forced-order sample; it does not establish automatic custody transfer or MAP01 completion. No source change or adoption decision is justified solely by this note.
