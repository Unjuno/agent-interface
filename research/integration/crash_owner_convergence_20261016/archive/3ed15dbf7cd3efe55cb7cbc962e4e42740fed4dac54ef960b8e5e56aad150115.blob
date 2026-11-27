# A34: same-key X11 source attribution across independent XTest clients

**H** — On one core X11 display, a process-owned XTest key hold and a second client's same-key XTest hold are not independently represented by the server keymap. Releasing the process owner's key may clear the global key state even while the second client still regards its hold as active.

**T** — One private TCP-disabled Xvfb display in a private mount namespace; valid MIT-MAGIC-COOKIE auth; actual `InputOwnerProcess` / V4 owner service sends KeyPress and verified KeyRelease; an independent second Xlib/XTest client also sends KeyPress for the same keycode while the owner hold is active; a third connection observes events and `query_keymap`. No GUI application, game, model, physical device, or shared X server.

**D** — `PASS_METHOD_SCOPED` if before external hold the global key state is down, the external client issues same-key KeyPress while logically retaining its hold, the actual owner service sends verified KeyRelease, an independent KeyRelease is observed, and the global keymap is up while the external client's test-side logical-hold flag remains true. This proves only that core X11/XTest state is not per-client attribution. `FAIL` if the global state remains down independently of owner KeyRelease. `STOP` on setup or observer failure.

**C** — A second XTest client is not a physical keyboard. It tests whether the core X11 input path exposes per-client state; it cannot establish physical-device behavior or the behavior of XI2/raw-input APIs.

**U** — No physical input or task effect. No conclusion about the frequency of concurrent external input. A PASS requires exclusive display/device ownership or a separate source-aware arbitration mechanism before an owner may release shared global state; it does not justify a live desktop release.

One frozen candidate invocation, no retries. Exact raw events, owner receipt, keymap samples, and hashes are retained. Allocation: `V39-X11-SHARED-KEY-SOURCE-A34-20261012-01`.

A33 stopped before any display connection because XAUTHORITY was passed only to Xvfb and not set in the candidate/client process. A34 sets both XAUTHORITY and DISPLAY in the parent environment, which is inherited by the real owner service and all observer clients. The source-attribution treatment and decision gate are unchanged; one invocation, no retries.



## Audit outcome

The sole invocation preserved raw candidate output with candidate pass=true, but the independent audit status is STOP_UNFROZEN_INVOCATION_AND_MISSING_EXTERNAL_PRESS_OBSERVATION. FREEZE.json was accidentally generated after invocation due to a PowerShell syntax failure; the external KeyPress event list was empty. Do not interpret this as a pass and do not repeat A34.
