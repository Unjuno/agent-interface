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
History is session-local and currently retained in memory until review or object disposal;
callers must bound session lifetime. No claim of unlimited-session memory use is
made. A dispatch/persistence exception can mean uncertain delivery; inspect the
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
Contract tests do not substitute for a completed fresh primary trial. Production
adoption and efficiency claims remain pending that validation.