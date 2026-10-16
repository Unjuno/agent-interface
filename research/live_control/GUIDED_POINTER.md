# Guided pointer reply pilot — 2026-09-13

Candidate `session_v15.py`, `input_owner_v9.py`, `pointer_reply_v2.py` and
`interactive_v12.py` connect a worker yield to one reply during the original
button hold. This follows Issue #2's bounded continuation direction. Existing
baseline entrypoints remain available; this candidate is not promoted or qualified.

## Contract

An ordinary submitted program can contain this step:

```json
{"op":"pointer_guided","points":[{"x":619,"y":390},{"x":631,"y":390}],"duration_ms":100,"reply_timeout_ms":1000,"max_updates":2,"feedback_delay_ms":80}
```

The initial path ends before yielding: there is no remaining preplanned tail
running concurrently with a correction. The worker publishes an observation and
`pointer_yield` with ticket, sequence and absolute reply deadline. Respond through
the candidate CLI with either command below, using the emitted ticket/sequence:

```json
{"op":"pointer_reply","ticket":"<ticket>","sequence":2,"command":{"op":"move","x":654,"y":390}}
{"op":"pointer_reply","ticket":"<next-ticket>","sequence":3,"command":{"op":"finish"}}
```

Only one reply is accepted per yield. Acceptance is not execution. Wrong sequence,
duplicate, obsolete and late replies are rejected. Movement must match the owner
instance/revision, original live lease and target, with one physically held owned
button and no held keys. The owner checks the reply deadline again immediately
before movement. Neither a reply nor a new observation renews the original lease.

Reply timeout is 100–5000 ms, updates 1–4 and optional feedback delay 0–250 ms.
The declared combined step budget is bounded by the existing 10-second budget.
After the final permitted correction the worker releases automatically. A finish
reply releases immediately. The reply timer remains armed after the worker consumes
the reply, until execution/finish acknowledgment clears it. Thus a stalled worker
cannot keep holding beyond the reply deadline just because it consumed a reply.

## Evidence

Three private Linux/X11 Inkscape cohorts use a scripted local red-bounding-box
controller reading decoded frames. This is a known fixture, not a remote model
trial or evidence of general visual reasoning. The saved SVG is used only for
independent final scoring, not to choose a correction.

| Cohort | Candidate | Requested / observed displacement | Exact frames | Guided program duration |
|---|---|---|---|---|
| 01 | session14 / reply v1 | 24 / 23 screen px | 12 | 557.2 ms |
| 02 | session15 / reply v2 | 24 / 23 screen px | 12 | 569.7 ms |
| 03 | session15 / reply v2 | 24 / 23 screen px | 15 | 542.0 ms |

All three satisfy the declared ±1 px tolerance and the legacy saved-object score.
The durations are local accepted-to-terminal measurements, excluding remote model
latency and the separate save/scoring program; they are not matched speedups over
previous open-loop trials. `audit_guided_pointer.py` checks 39 exact reconstructed
frames, listed source hashes, saved SVG scoring, terminal release verification,
late-motion absence and owned-process cleanup. Manifests cover listed sources,
not every transitive environment dependency.

Each cohort also tests output blocked at yield: missing replies release by the
reply deadline (`needs_decision`), and original lease expiry releases (`expired`).
Late replies cannot move. Cohort 03 additionally accepts and consumes a reply,
stalls the worker before owner admission, and verifies independent release and
rejection after resumption. Its terminal remains `failed` with obsolete-owner/revision
error; recovery classification is unfinished. A subsequent observe program completes.

Prototype cohort 01 is retained: its mailbox cleared the timer on consumption,
leaving an execution gap. Cohorts 02/03 retain the timer through execution and add
owner-side reply-deadline checks. The `guided-cli-01` smoke verifies advertised
operations, obsolete-reply rejection and clean exit. Its xterm task score is false
because no typing task was attempted; it is only a protocol smoke test.

## Remaining limits

Historical image/state samples are not atomic and do not prove current GUI state.
A blocked capture/delivery before a reply offer is protected by the original lease,
not a reply timer that has not yet been created. Finite timers are bounds, not
real-time scheduling guarantees. Remote assistant use, fresh layouts, collateral
scoring across domains, token cost and matched baseline comparisons remain pending.
This is shared-runtime semantic churn, not a qualifying research-freeze revision.
