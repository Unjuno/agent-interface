# Current owner RPC v2 implementation plan

Goal: repair the two reproduced #8876 adoption gaps in an explicit private-socket
service boundary around the current strict process-identity owner. This is one
implementation step toward external session ownership, not the full goal.
Spec: research/integration/crash_owner_convergence_20261016/README.md and the
current target_process_identity_v1.valid_source/InputOwner v12 lease contract.

Architecture: input_owner_rpc_v2.py exposes encode_lease/decode_lease and
OwnerRpcClient(socket, display, service_id, timeout), serve_owner(socket, owner,
display, service_id). Caller supplies an already connected, exclusively owned
private socket and existing owner; this module launches nothing. Exact schemas,
IDs, original lease deadlines and source bindings are enforced. All responses
are bounded frames; uncertain outcomes permanently quarantine the client and
close only detaches that transport. Server EOF/failure closes its existing
owner and returns a separate release/stop receipt through the service function.
Window-lifecycle use is explicitly refused pending a cross-process canonical
observer contract. Existing default session/controller selection is unchanged.

Constraints: no native GUI/game/provider/model/WSL/container execution. Ordinary
loopback socketpair and the existing selected-backend Fake X fixture only.
No physical release-time bound or cross-process clock qualification is claimed.
No hidden socket opener, process launcher, input fallback or retry. One socket
has one serialized client caller and one service; max frames/requests/leases
are bounded. Timeout covers send/receive and lock admission. Cleanup must remain
possible after failure without sending another framed input request.

- [x] Add test_input_owner_rpc_v2.py. First assert the absent implementation;
  preserve red output. Require codec identity preservation, strict original
  binding, native strict-owner positive/refusal, real socket request/reply,
  duplicate/stale ID/lease refusal, EOF release, partial reply/timeout/wrong-ID/
  malformed reply sticky quarantine, no post-error send, unsupported window
  rejection and an explicit unverified-cleanup result for a blocked release.
- [x] Implement input_owner_rpc_v2.py from those requirements. Validate the
  service's actual process-aware owner before readiness; refuse old schema,
  unknown fields, changed lease sources/deadlines, expired input admission,
  duplicate JSON members, invalid values and incompatible capabilities.
- [x] Run exact selected tests normal/-O, plus existing process-identity backend
  and owner regression modules. Preserve commands, source pins, outputs and
  first failures in a new additive packet. Independently read raw socket rows
  and verify bytes, IDs, source joins, no second send and release limitations.
- [ ] Review immutable patch, verify real protection/local checks, integrate.
  Return evidence and actual remaining session/controller/process-death work
  to#59. Keep the full computer-control goal active.

Review focus: late input after a lost response; blocked native cleanup; shared
window epoch falsely advertised across processes; source replacement under one
intent; a local transport close incorrectly treated as verified release.
Each condition needs a discriminating negative or positive control. Do not
turn this plan into an additional worker approval/quorum gate.
