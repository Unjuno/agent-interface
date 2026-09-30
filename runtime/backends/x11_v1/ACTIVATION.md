# Explicit window activation

`focus` preserves input focus within the target window, including a focused child.
It does not promise to bring an obscured window to the front. Multi-application
workflows can instead request the optional `window.activate` capability:

```json
{"op":"activate","target":"inkscape","timeout_ms":500}
```

This operation uses the existing program admission, target registry, source
revision and lease checks. It is not a separate input bypass. The target must be
a registered, managed X11 client. The X11 window manager must advertise EWMH
`_NET_ACTIVE_WINDOW` support. Other backends report this capability unsupported;
it is not part of the portable office floor.

The backend sends one activation request and polls for both the active client
and input focus within that target. `timeout_ms` is required, an integer from
0 through 2000. It is a polling budget, not a deadline on blocking X11 transport
requests. A timeout stops the remaining program and attempts input release.
The window manager may still apply the request later. There is no automatic
retry, direct raise fallback, or replay of the remaining editing operations.

The raw execution receipt includes `activations`, with operation index, target,
window ID, request-attempt flag, timestamps, last active-window IDs, focus check
and status. `active_and_focused` is a momentary window-manager/focus observation.
`visual_confirmation` remains false: it does not prove visible pixels, selected
editing controls, application readiness, or completion of any edit.

In a staged workflow, activate and capture first, review the returned image,
then explicitly select the editing region if needed before issuing edits.
Use a fresh observation to resolve ambiguous feedback before repeating an edit.
The existing `wait_update` remains a fixed delay, not an application completion
acknowledgement.

Integration evidence is retained in the
[published evidence bundle](../../results/explicit-window-activation-01/README.md), including
`results-local/two-app-primary-01` (focus-only switching failure),
`results-local/explicit-window-activation-primary-01` (correct saved files but
experiment driver failed during close), and
`results-local/explicit-window-activation-primary-02` (one staged two-app trial
with correct saved files and verified explicit close). Different seeds and policies mean
they are not a controlled speed comparison. No model-token or human-tempo result
has been established by these trials.
