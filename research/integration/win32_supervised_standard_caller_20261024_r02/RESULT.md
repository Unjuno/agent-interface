# R02 result: PASS for the frozen narrow question

The original pre-run audit script produced 12/14 because it required the public
dispatch response to be immediately `returned` and expected `call_id` inside the
action object. R02's predeclared procedure explicitly allows a pending dispatch
followed by retrieval of that same call. A supplemental audit v2 checked the
pending response, the identical call ID in the retained `returned` report and
terminal `interface_results` row, and the completed action. It passed 15/15;
the original `audit.json` remains unchanged as the first audit output.

Public observation and the locally inspected owned HWND had the same generation.
One public dispatch returned `pending` after 10.011 seconds; repeated read-only
`interface_results` calls retrieved the same call as completed. The operation's
input execution window was 47 ms, the producer exited 94 ms after execution
started, and independent neutral-state readback followed 16 ms after that exit.
The release receipt was verified with empty down/unknown key and button sets.
The fixture journal recorded the exact click, every character of
`SUPERVISED-MCP-OK-20261024-R02`, and one save event; its independent effect file
matched the frozen expected effect. The fixture exited cleanly, the prior
foreground window was restored, the supervised session closed, and task success
remained `null` in the runtime.

The runtime retained `input_dispatched: null` even though execution reported 70
accepted emissions and the independent fixture journal showed the effect. This
caller summary gap is a separate integration defect; commit `5da333c` did not
repair it. The next attempt is reserved to verify the corrected field. The
10.011 second wait to the first response also remains a latency observation,
not a matched efficiency result. The copied R02 probe also retained the literal
R01 lease ID label inside its fresh session; R02's actual session, call, and
operation IDs are separately recorded in raw. R03/R04 use attempt-specific
lease labels.

R02 establishes one successful standard-caller generation-to-effect path with
verified release and independent neutral readback. It does not establish a
hard release deadline, recovery under blocked I/O, MAP01, runtime task-success
integration, matched efficiency, or broad reliability. It used no WSLc or
Docker allocation.
