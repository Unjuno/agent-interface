# Effect-owner receipt through existing event envelope v1

Decision: **RETAIN_EXISTING_EFFECT_EVIDENCE_ENVELOPE_SCOPED**.

## Question
The merged owner-binding construction derives `invariant_manifest_id` from a durable effect-owner receipt, but its report leaves one concrete integration step: carry that receipt through an existing caller/executor event boundary without permitting an adapter to synthesize or replace the binding. The current event path already scopes `effect_evidence` by action/request identity. Should a new receipt event be added, or can the owner receipt travel inside the existing envelope?

## Container-first method
The repository was not used as the experiment runtime. Exact current-main bytes were reconstructed in the container and verified by Git blob/SHA identity for `effect_outcome_contract_v3/outcome.py`, owner-binding `owner.py`/`bridge.py`, and `event_scope.py`, `request_boundary_v2.py`, `event_cursor_v5.py`. The tested upstream identities are recorded in `formal_plan.json`.

Two envelope policies were compared over three existing EventCursor read scopes:
- `new_event`: standalone `effect_owner_execution_receipt` event;
- `effect_evidence`: existing `effect_evidence` event with an `owner_execution_receipt` nested under `effect`.

Scopes: unscoped, action-scoped, request-scoped. Five repetitions per cell = 30 first outcomes. Local premeasurement freeze `6313be34c70dbb641d872d559cb883edce2f569c`; plan SHA-256 `7baaa7a85c3610796349670b2ccc3d26c20218a8fd016029d87676dedd07683f`. No measured-ID rerun.

## Results
| envelope | unscoped | action-scoped | request-scoped |
|---|---:|---:|---:|
| new event | 5/5 retrieved | **0/5 rejected** | **0/5 rejected** |
| existing `effect_evidence` | **5/5 retrieved + classified** | **5/5 retrieved + classified** | **5/5 retrieved + classified** |

The standalone new event is stored and returned by unscoped EventCursor reads, but current `validate_scope` rejects that event name for action-scoped reads and request-scoped reads reject it because it is not in `SUPPORTED`. The existing `effect_evidence` envelope is already admitted by both scope systems. Its nested receipt survives JSON/EventCursor roundtrip exactly at the semantic field level and is then revalidated against the durable owner receipt before the exact merged outcome-v3 reducer classifies the wrong+compensated trace as `EFFECT_CONTRADICTED_COMPENSATED`.

This favors an adapter inside the existing effect-evidence vocabulary rather than a new event type. It is an integration result, not a production ABI decision.

## Negative controls
A separate adapter matrix retained before this envelope study showed owner receipt manifest/sequence/value substitution and caller manifest replacement all reject, while exact replay remains one effect. In this envelope block, posthoc strict audit recomputes authoritative owner DB state, scoped returned records, nested receipt fields, and outcome classification. Five copied-evidence corruptions (nested manifest, boundary status, owner DB receipt, classification label, duplicate effect) all reject.

## Verification
- formal cases: 30/30 first outcomes;
- frozen audit evidence integrity: 30/30;
- posthoc strict audit: 30/30;
- tests: 6/6 before freeze and 6/6 after extraction;
- archive manifest: 87 files, 0 mismatches;
- frozen and strict audit replay: byte-identical;
- same measured ID reruns: 0;
- raw archive: 37,072 bytes, SHA-256 `cbbda3bdbd65bbed8f95300fc331631176fba38bbe3bea7250be31b82b25730f`.

## H/T/D/C/U
**H:** adding a new effect-owner receipt event unnecessarily breaks existing scoped EventCursor vocabulary, while nesting the owner receipt in the already-scoped `effect_evidence` record can preserve receipt identity through the caller boundary.

**T:** exact current-main EventCursor/scope code + exact merged v3/owner bridge; 2 envelopes x 3 scopes x 5 first outcomes.

**D:** retain existing `effect_evidence` envelope as the smaller integration adapter shape at this scope.

**C:** a different design could explicitly extend both action- and request-scoped vocabularies with a new event type. That may be appropriate if lifecycle semantics require a separate boundary; this experiment only shows it is unnecessary for the tested receipt transport.

**U:** no live subprocess socket, no X11/model/GUI, no shared-runtime modification, no hostile same-user transport, no authentication or performance measurement. `event_socket_v11.py` source shows child stdout records are appended to EventCursor unchanged, but this formal block directly executes EventCursor rather than a live Unix-socket subprocess.

## Integration implication
The next integration step should be a small adapter/regression in the #57 composed path: emit owner receipt data within the existing `effect_evidence` record and have the caller derive/verify outcome only from the receipt-backed fields. Do not add a parallel receipt event namespace unless a concrete lifecycle requirement demands it.
