# Independent input owner: interactive integration and assistant use

`interactive_v6.py` is the current research CLI. It uses the measured
`session_v5.Backend`, creates the input owner before the control loop, closes the
executor before closing that owner, saves owner release records, and then tears
down the private application/Xvfb session. A `clock` request returns the runtime
monotonic timestamp and current observation sequence. Clock freshness is not
screen freshness; it does not refresh or validate the observed target.

Three actual assistant sessions are retained, with screen inspection and actions
chosen in this conversation rather than a prerecorded controller:

| Archive | Revision | Outcome |
|---|---|---|
| owner-assistant-01, XTerm seed 920101 | interactive v5 | Typed/saved t920101; independent saved text correct |
| owner-assistant-02, Calc seed 920102 | interactive v5 | Failed: assistant put 310 in B1 instead of required A2; saved A1/A2 were 196/null |
| owner-assistant-03, Calc seed 920103 | interactive v6 | A1=330 and A2=770; Excel format confirmed; independent saved workbook correct |

The failure is a task-understanding error, not a demonstrated input-owner
failure. Revision 5 inherited a ready message containing values `a`/`b` without
cell destinations. The assistant assumed a horizontal layout. Revision 6 adds
an explicit human-readable task to ready messages. The successful follow-up
also benefits from the assistant learning the task, so it is not an isolated
causal evaluation of that message change. Frozen revision 5 and the failure
remain available.

All six accepted programs completed with verified release. All three owner
shutdowns verified release; all processes returned exit code zero. Eighteen
packet frames match archived PNG pixels exactly. The audit independently reads
the saved text/workbooks and reproduces both success and failure outcomes.
Acceptance-to-first-image-ready local intervals were 93.5–165.8 ms. These include
logging/PTY behavior and are not a matched comparison, model response time or
proof of human-like tempo. Text output is still verbose and synchronous.

The Calc confirm screenshots also expose temporal skew: a captured image can
still show the dialog while the subsequently queried window list no longer
contains it. In the final successful trial the assistant explicitly requested
another observation and inspected the dialog-free sheet. Image and context have
separate timestamps; neither program completion nor window disappearance alone
proves a file was saved. Saved-output evaluation supplies the task result.

## Reproduce

From this folder under the documented Ubuntu/WSL environment:

```sh
python3 interactive_v6.py --app calc --seed 920201 --out ../../results-local/owner-new
python3 audit_owner_sessions.py results/owner-assistant-01 results/owner-assistant-02 results/owner-assistant-03
```

Use newline-delimited `submit`, `cancel`, `clock`, and `finish` commands as in
the earlier lease CLI. Each submission still requires a fresh identifier,
`expected_sequence` and an absolute runtime-clock `valid_until_ns` no more than
30 seconds ahead. The new script preserves the earlier operation vocabulary.
No semantic focus guard or automatic resynchronization has been added.

Next: instrument/handle image-context skew and focus changes; reduce blocking
notification work; compare the same planner on matched tasks. Owner connection
failure, shutdown timeouts and supervision still need work before service use.
These three runs did not inject stalls or disconnects; the earlier stall probe
remains the separate evidence for expiry during blocked observation/logging.
