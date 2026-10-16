# Request-scoped retained finalization status

The preceding live evaluator-failure probe could query retained status only
sequentially because status events had no query identity. Candidate interactive
v27 adds the existing bounded runtime correlation fields to finalization_status:
transport_request_id, runtime_request_sequence and command_op. The status query
is not an admitted input action, so declared_action_id remains null. The retained
outcome's final_program still identifies the evaluated program separately.

request_boundary_v2 supports finalization_status as a query-scoped event;
EventCursor v5 and socket v11 select this candidate. A caller can send a status
command with request_id and wait with the same read_request_id. Intervening
records remain in the returned prefix. No admission, scoring, timeout, cursor
retention, or deduplication behavior is changed. Older versions remain frozen.

The live status-correlation-01 probe injects the same evaluator exception after
ordinary private X11 input. The common outcome wait returns pending, then two
sequential and two concurrent status queries recover the retained error. Each
concurrent query returns its own transport identity and distinct runtime receive
ordinal. Both snapshots have the same finalization outcome. Repeating an existing
query ID returns its prior reply with replayed=true, with no new runtime query.

One actual submit, verified input release, three exact frames and every returned
batch's contiguous delivery slice are audited. The correct saved token is checked
after cleanup but does not become a runtime evaluation result. Final task success
stays unset. The process exits zero and removes its socket. Retained error time
is 15.220 ms after terminal; the first status socket return is 234.207 ms after
terminal including the deliberate 200 ms outcome wait. This is not a speedup
comparison with the preceding uncontrolled run.

Four additional status-boundary controls verify matching identity, unrelated
identity yielding timeout, missing identity yielding identity_unknown, and an
unrelated available snapshot retained before a matching pending snapshot. A
matching query response can legitimately be pending: identity does not establish
completion, success, or that its retained program is the caller's desired one.

Important caller rule: retry an uncertain query using its same request ID, but
use a NEW request ID to request a fresh snapshot. Session-local deduplication
deliberately preserves an earlier pending response on exact replay. Automatic
fallback orchestration is not implemented here; it must verify final_program,
retain evidence and distinguish pending, error and evaluated results. Identity
is session-local metadata, not authentication or restart-safe causality.

Evidence: results/status-correlation-01 and results/status-boundary-01, with
source manifests, socket records, raw images and saved output. This is scripted
fault injection, not actual assistant latency or token measurement. No default
promotion. Next integrate a bounded, identity-checked status fallback into the
caller and test pending-to-available transitions with fresh query IDs.
