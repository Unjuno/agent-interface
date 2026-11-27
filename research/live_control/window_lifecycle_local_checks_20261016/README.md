# Direct-window lifecycle through the standard guarded MCP caller

Base `36035ea7ed783897919f7399afb51abef7bbc75d`; tested code
`56a0fef474de46d6dfed19e580f50b9d9291e71a`. Production implementation first pinned at
`f96c1ecf848179c25c6353ed44f2776e57f885bb`; the later commit adds two persistence
controls and clarifies intermediate-file semantics. This is ordinary Fake X construction,
not a formal/live allocation. Initial RED, intermediate checks and final logs are
preserved. Initial RED test revisions were not committed separately; those logs
are repair history, while the final eight Python sources are pinned bytewise and
joined to the worktree by AST in `SOURCE_PINS.json`.

## Result and decision

Adopt the explicit opt-in guarded MCP path within construction scope. A
process-only control still accepts an old alias despite injected destruction
with unchanged process digest, XID, geometry and pixels. The selected lifecycle
policy refuses it; destruction after the modifier releases that prefix and
blocks the following key. Healthy and reparent/remap cases complete. This uses
the actual owner, bridge/history/handles, query worker, dispatch/session and
backend methods, with X transport/emission and initial backend setup replaced.

The persistent reader selects StructureNotify on the target itself and checks
its own mask after round trips. Destroy, missing coverage, malformed/synthetic
events, transport failure or a 256-event budget overflow cause sticky refusal.
New readers produce distinct opaque continuity tokens. The root-only historical
#3950 tracker is neither installed nor rerun.
Direct-client subscription is established prior work, also discussed in
[#4008](https://github.com/Unjuno/agent-interface/issues/4008) and its #777
predecessor. #4008 distinguishes replacing a shared event mask from union or
separate-connection ownership. This change uses the existing dedicated query
client and checks its own mask; its new scope is the standard caller's binding/
pre-press/cleanup integration, not discovery of direct subscriptions.

Cancellation and expiry controls hold CTRL in the fake keymap while a lifecycle
query is blocked. The caller returns with verified empty release before the gate
opens. After the late reply, the same client closes, owner sequence is unchanged,
and new input is refused. Both active visual isolation and qualified persistence
retain the lifecycle token. Capture-time destruction publishes no new sequence/
history. Activation also checks the retained token after request preparation.
With the trusted additional-input guard recapturing before the next chord key,
blocked qualification persistence also permits cancellation/expiry release before
the save resumes. Late persisted files remain intermediate; they do not advance
owner history. The first persistence test fixture lacked that recapture path;
its failed gate waits are retained alongside the corrected fixture.

| Executed validation | Normal | Optimized |
|---|---:|---:|
| New direct-reader + public-caller methods | 19 pass (included below) | 19 pass (included below) |
| Guarded X11 suite | 136 pass | 136 pass |
| CLI/MCP suite | 420 collected, 5 platform skips, no failures | 420 collected, 5 platform skips, no failures |
| Committed-source distribution/archive suite | 21 pass at f96c1ec; production source unchanged afterward | not separately run |

Timings in logs are diagnostic. This is not a latency/resource comparison or a
probability estimate. Fake clocks/emission ledgers are test controls, not physical
measurements. No live display, input, game, model, VM/container or WSLc allocation
ran. Ordinary regression tests were not treated as consumed formal experiments.

## Contract, replay and limits

See [the public contract](../../../runtime/guarded_x11_v1/WINDOW_LIFECYCLE.md)
for selection, source fields and persistence paths. Recheck construction with:

```text
python -B -m unittest runtime.guarded_x11_v1.test_window_lifecycle runtime.cli_v1.test_mcp_window_lifecycle -v
python -B -O -m unittest runtime.guarded_x11_v1.test_window_lifecycle runtime.cli_v1.test_mcp_window_lifecycle -v
```

The X11 [event specification](https://www.x.org/releases/X11R7.6/doc/libX11/specs/libX11/libX11.html)
supports direct-target Destroy/Reparent subscription semantics; installed Xlib
field definitions were inspected. No native server exercised those semantics
here. Trusted server, honest events, reliable ordered connection and exclusive
reader use remain assumptions; arbitrary undetected loss is not covered.
Destruction between the last check and XTEST is still a race. Native input send/
readback stalls and physical release bounds remain unresolved. So do task effect,
bounded task recovery and matched economics. MAP01/V12 receives no lifecycle
adapter from this change; it needs its own integration and qualification.

Next decision: transfer this evidence contract to the chosen MAP01 input owner
without weakening cancellation/release, or qualify a fresh native direct-window
case when authorized. Do not repeat consumed #3950/#4039 allocations. #5/#17/#59/
#57 remain open in their unresolved scopes. This change adds no reviewer quota,
global assignment or new coordination service.
