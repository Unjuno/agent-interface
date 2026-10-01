# V39 detectability posthoc — versioned clock/availability correction

**Correction status:** interpretation-only correction to the preserved first
outcome. `RESULT.json`, `RESULT.md`, `VISUAL_READ.json`, the frozen source,
and the retained raw evidence are intentionally unchanged. This note does not
rerun or alter the experiment.

## Evidence and correction

In `research/doom/session_map01_v12.py`, `emit_ns` is sampled before JSON
serialization and before either event-log write (lines 97–108 at the reviewed
head). The controller retains this producer field but has no receive or
dequeue timestamp (`map01_overlap_controller_v39.py`, lines 486–500 at that
head). Therefore the frozen artifacts establish producer emission, not
controller receipt, delivery, availability, or consumption.

Apply these corrected semantics when reading the original artifacts:

| Frozen name or wording | Corrected interpretation |
| --- | --- |
| `latest_typed_state_available_before_request` | `latest_typed_state_emitted_before_request`; seq 71 is the latest producer-emitted typed state before the request, not proven available to or consumed by the controller. |
| `request_to_first_loss_delivery_ms` | `request_to_first_loss_emit_ms` = 1,488.187597 ms, computed from the request journal timestamp to producer `emit_ns`. Controller receipt/consumption is unmeasured. |
| RESULT.md “last typed state already delivered” / “delivered 1,488.187597 ms” | Read as “latest typed state producer-emitted before request” / “first health-loss observation producer-emitted 1,488.187597 ms after request.” |
| VISUAL_READ.json seq 71 “last delivered state” | The image/typed event is a retained producer-emitted observation; it is not proof of controller receipt or consumption. |
| PR summary’s delivery-time wording | Interpret as producer-emission timing only; do not infer controller-visible latency or an intervention margin. |

The 1,474.923434 ms capture interval remains a capture-time subtraction. The
1,488.187597 ms value remains an emission-time subtraction. Neither is a
measured delivery latency, controller availability interval, or safety margin.
The request/action source is seq 70; seq 71 is only the latest
producer-emitted typed state before the request. The original HOLD remains
`HOLD_NO_EFFECTIVE_INTERVENTION_BOUND_V39_CELL`, and the intervention/harm
endpoints remain null.

## Scope

This corrects clock and availability terminology only. It does not change the
first frozen result, raw bytes, event order, measurements, or classification;
it supplies no controller receive timestamp, causal claim, or new experiment.
