# Scoped X11 Python API

The portable runtime includes the same scoped target handles and guarded input
implementation used by the native research callers. This is an explicit Linux/X11
API requiring Pillow and python-xlib. It does not open a connection on import and
is not a cross-platform handle API. An opt-in public MCP mode is described below.

```python
import sys
sys.path.insert(0, "/absolute/agent-interface-runtime.pyz")
from runtime.guarded_x11_v1.bridge import NativeHandleBridge

bridge = NativeHandleBridge(":99", {"app": explicit_window_id}, "app",
                            "/absolute/fresh-receipt-directory")
try:
    observation = bridge.observe()
    # Present observation["native"]'s image to the caller before choosing a point.
    # caller_point is an explicit integer screen point grounded in that image.
    offset = bridge.mint("save", observation["sequence"], caller_point,
                         region_size=(24, 14))
    result = bridge.click("save", offset,
        tail=[{"op": "wait_update", "timeout_ms": 100}])
    # Review the result and a fresh observation; program completion is not task success.
finally:
    bridge.close()
```

The display, window ID, output directory, grounded point and wait are caller
choices. Existing source capture, scope, texture, exact-pixel matching, bounded
window translation and fresh guards remain unchanged. Missing/stale/changed
references refuse input; they never trigger automatic grounding or replay.
`keyboard(alias, offset, tail=...)` guards keyboard continuation without clicking.
`review_window(window_id)` explicitly revokes all old aliases even when review
fails; successful review does not infer semantic equivalence of windows.
Call `close()` in a finally block. It closes this connection, not the application.
The object is synchronous and intended for one caller; it is not a concurrent queue.

Observations and raw input receipts are retained in the fresh output directory.
History is session-local. At most two decoded full-screen images are retained
by its cache; older observations reload their exact hash-checked PNG when needed
for explicit grounding. Reloading never captures the current screen or changes
the source sequence. Missing or corrupt old artifacts refuse grounding. Recent
cached images remain the pixels already verified at capture. Metadata, handle
patches, caller-held images and disk artifacts are not bounded by this cache;
callers must still bound session lifetime. Window review clears all old history
without loading artifacts. No unlimited-session memory claim is made. A dispatch/persistence exception can mean uncertain delivery; inspect the
retained evidence and observe explicitly instead of replaying input.

`runtime.guarded_x11_v1.form.fill_and_submit` is the existing two-target fixture
method. It retains each step through mandatory `on_step`, checks completed
execution and verified empty releases before proceeding, and returns
`task_success=None`. It does **not** verify the entered text before Submit and
must not be treated as a general semantic form transaction. See the
[native method contract](../../research/live_control/NATIVE_GUARDED_FORM.md).

Research module names remain compatibility entry points to these exact classes
and functions. The portable archive contains no research modules, fixtures or
model calls. Packaging this API establishes availability, not faster operation,
reduced tokens, semantic completion or human-tempo performance.

New research source manifests must record the implementation here as well as
compatibility wrappers. The read-only
[`complete_guarded_hashes`](../../research/live_control/guarded_source_dependencies_v1.py)
helper completes known wrapper-based manifests and refuses conflicting pins.
Historical frozen results require their original recorded source; they are not
silently rebound to current main. See the
[source-provenance integration evidence](../results/guarded-source-provenance-01/README.md).

## Explicit public guarded MCP mode

The public MCP server can expose this shared implementation with
`--session-mode guarded-x11`. Exactly one target must be configured. It adds
`interface_guarded_observe`, `interface_guarded_mint`,
`interface_guarded_input` and `interface_guarded_review_window`, using the
existing retained requests/results, busy lock and `interface_close` lifecycle.
Ordinary dispatch and transient-family review tools are not registered in this
mode. Existing default and persistent modes are unchanged.

```sh
python runtime.pyz mcp --targets /absolute/targets.json --output-directory /absolute/fresh-calls --display :99 --session-mode guarded-x11
```

The target file maps one caller-selected alias to its explicit X11 window ID.
Observe and view the image, mint a point with that source sequence, then issue
input with the returned alias/offset. Review the returned input receipt and image
separately. Capturing after input does not wait for a redraw; `wait_update` is a
bounded delay, not semantic acknowledgement. In particular, address-field focus
or CTRL+A emission does not prove readiness or selection. Verify entered text
before a consequential submission. No automatic polling, semantic action
selection, or input replay is introduced.

`interface_results` retrieves retained evidence without new input, including
after close. Guarded reports remain full reports, regardless of compact result
options. Explicit window review revokes old aliases; it uses the bridge's
focused-window contract, not authenticated identity or transient-family review.

The first public-MCP primary trial was interrupted and has invalid review-source
attribution; see [preserved evidence](../results/guarded-mcp-primary-interrupted-01/README.md).
A fresh [completed primary trial](../results/guarded-mcp-primary-02/README.md)
subsequently verified six exact saves and explicit recovery through the public
mode. This supports opt-in integration; efficiency claims remain unproven.

## Explicit activation before a new guarded action

After loss of target focus, Python callers may explicitly request
`bridge.activate_window(window_id=..., source_sequence=...,
current_binding_revision=..., expires_at_ns=..., timeout_ms=...)`; MCP callers
use `interface_guarded_activate_window` with the same required fields. Only the
currently registered window and latest delivered source/current revision are
accepted. The caller supplies its expiry on `interface_clock`'s execution-host
clock. The existing core lease/capability checks still apply.

Activation sends an EWMH request, not text/clicks. Successful or uncertain
activation blocks guarded editing until explicit window review. Review that
image, mint a new alias and choose a new action; no old program is replayed.
Core refusal preserves any earlier review block. No strict caller STOP is
cleared. The WM may act later after a timeout. `timeout_ms` is 0..2000 and is
a polling budget, not a deadline on blocking X11 transport. Managed-client/EWMH
support is required; within-target editing focus and already-held input remain
outside this operation. See [main-specific integration evidence](../results/guarded-activation-main-01/README.md).

Public MCP optionally accepts `review_after_activation=true`. This explicitly
composes activation with the existing window review in the same worker call,
only after activation completes with verified neutral input release. The default
is false. The response retains the activation result separately from review,
returns the exact review image, and publishes the new binding revision. A failed
or uncertain activation never triggers review. A review exception preserves the
activation receipt and blocks editing; it never claims that no effect occurred.
The caller must inspect the returned image before fresh grounding and editing.
This removes a separate review request from this chosen flow; it does not prove
lower semantic latency, human tempo or token cost and performs no automatic input.

### Deadline enforcement

The existing five-second guarded lease includes admission captures, pointer
checks, typing and explicit waits. Every new key press now checks that deadline;
key release remains permitted afterward. A fixed wait ends at the earlier of
its requested end or the original lease deadline, without renewing the lease.
At expiry, execution fails, retains the completed prefix and interrupted wait,
attempts release and does not start the remaining input. The public guarded
MCP default still returns one post-result observation, including after this
failure. Inspect partial effects and the image before choosing a new action;
never replay the whole tail automatically.

This is cooperative enforcement on the guarded X11 path, not a hard real-time
stop. Scheduling or blocking X11 calls can delay detection and physical release.
It adds no continuous focus sensor or autonomous input owner. The ordinary X11
backend's fixed-delay behavior and admission-only lease check are unchanged.
A completed fixed delay still does not acknowledge application redraw.

Guarded observations use the RGB pixels from the current PNG producer after verifying that saved PNG and its raw-capture link. The private handoff is consumed once; fresh capture and every guard check remain. [Primary use and retained checks](../results/capture-rgb-handoff-01/README.md) documents the removed decode round trip, corruption refusals and timing limits.
# Explicit hover and finite reference deadlines

`NativeHandleBridge.move(alias, offset, tail=...)` and the public
`interface_guarded_input(interaction="move")` move the pointer without pressing.
The tail permits only waits and observations. Hover may change pixels: review
the resulting image and explicitly ground a new alias before clicking. This
does not weaken pixel guards, choose an action, or automatically retry input.

Public mint replies now include `lifetime`: the execution host's monotonic
mint time, actual alias expiry, and capture freshness limit. Compare only with
that same host's clock. Reading retained results does not renew the deadline;
an unexpired alias still requires fresh pixels, focus and ordinary admission.
Python `mint` retains its offset-only return; `mint_reference` includes metadata.
