# Owned owner-process v3 implementation plan

Goal: place the qualified current-owner RPC v2 in an independently owned spawned
Python process and retain file-fsynced, exclusive, identity-bound recovery evidence.
Spec: research/live_control/INPUT_OWNER_RPC_V2.md and#59's current service/death gap.
This step does not change default session/controller or claim native/game effects.

Files: research/live_control/input_owner_process_v3.py (spawn/identity/receipt),
research/live_control/test_input_owner_process_v3.py (owned-process Fake X cases),
research/integration/owned_owner_process_v3_20261016/ (conditions/raw/readback).

API: launch_owner_service(display, out, _owner_factory=None, startup_timeout=5)
returns OwnedOwnerService with take_socket() exactly once, startup metadata,
process handle, close_channel(), wait(timeout). Parent can create OwnerRpcClient
from the returned private socket or transfer it to one explicitly owned client
process. Only spawn context is used; the service inherits no parent client socket.
Default factory constructs current process-aware transition/native owner; tests
supply the named Fake X context factory. No RPC carries arbitrary code/callables.

Unique output directory and logical service generation are created per launch.
Startup records actual Python PID/PPID, supervisor PID, nonce and owner ID. Parent
joins this to its exact multiprocessing.Process handle (allowing the Windows venv
launcher PID/actual-interpreter parent relation); it never kills by reported PID.
This is owned-handle/logical-generation binding, not native PID creation-time proof.
Publish files by exclusive hard-link from a file-fsynced private temporary file,
then directory fsync where supported. Windows directory persistence across power
loss is unqualified. No final file is overwritten; checksum joins bind receipts.

Service returns initial recovery evidence before retiring its owner context. If
owner stop is unresolved, retain the process until its existing thread stops;
parent wait is finite and returns unverified/alive custody. Settlement is separate
and never upgrades the initial unverified result. Final success additionally
requires context teardown, matching finish/initial/startup bytes and exit0 of the
owned process handle. Missing/wrong-generation/partial/error records fail closed.
No automatic terminate, replacement or new input after unknown state.

- [ ] Write tests and preserve absent-module red. Verify normal close; client
  process kill causes EOF/release while service survives; service kill has no
  acceptable receipt; blocked Fake X release retains live custody then settles
  without verification upgrade; wrong generation/file substitution rejects;
  existing paths cannot be overwritten. Assert all owned children joined at end.
- [ ] Implement launcher, child entry and pure receipt validation. Preserve
  startup/publication/context failures and never accept file alone as process exit.
- [ ] Run selected current RPC/native/backend regression normal/-O with guarded
  driver (spawn must not rerun tests at import). Save startup/edge/receipt bytes,
  commands, outcomes, loaded-source pins and actual/launcher PID joins.
- [ ] Independently read records/altered negatives; review immutable patch,
  integrate using actual protection/local checks and return residuals under#59.

Review focus: inherited peer socket prevents EOF; PID reuse/logical-ID confusion;
verified receipt before failed context cleanup; blocked owner lost on process exit;
late settlement erases first unknown. No real display, WSL/container, game/model
or physical input during these ordinary owned-process constructions.
