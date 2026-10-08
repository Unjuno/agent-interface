# Existing scoped target handles connected to the native X11 session

2026-09-19. Two primary-assistant runs used the experimental
`research/live_control/native_handle_bridge_v1.py` bridge. The assistant viewed
each run's full-screen native `before.png`, chose point `[210,145]` in the input
field, and supplied `guard991081` / `guard991082`. Independent fixture files and
the final native read-only images confirmed both exact saves. No helper model
ran; primary-conversation usage remains unavailable.

The bridge reuses `scoped_target_handle_v3.TargetHandleStore` and its existing
v1/v2 pixel/scoping checks without modifying those frozen modules. It owns a
native X11 connection and calls the promoted `X11RuntimeSession` for admission,
input and release. It is a research adapter, not a promoted public JSON API.

Each successful click has four fresh, retained checks: before admission, before
focus, before pointer movement and before button press. Native captured PNG
hashes are linked to the exact raw observations passed to the resolver. An
explicit source sequence selects the image used for minting; no latest-file
lookup supplies the grounding. This source selection does not itself attest
that a model viewed the image; that occurred in this conversation.

In run 2, after the successful save, a deliberate private-Xvfb focus change
invalidated the old handle. A subsequent click request with a `mustnotrun` text
tail returned SCOPE_MISMATCH before native dispatch, with zero emission delta.
This is a controlled **focus** invalidation, not a layout-repair demonstration.

| One-run timing (ms) | Run 1 | Run 2 |
|---|---:|---:|
| Mint plus guarded native execution | 227.840679 | 243.502786 |
| Start through independent saved-effect read | 248.057388 | 256.700166 |
| Entire harness including assistant wait | 39389.343760 | 23480.959726 |

The timing field is named `dispatch_elapsed_ms` by the shared harness, but in
this mode includes minting and all guard captures. It is not comparable to the
earlier unguarded timing without a matched experiment. All native input ended
with verified empty release; private processes were reaped. No speed, token
saving, human-tempo or product-completion claim is made.

Actual executed bridge programs are `run-*/bridge/program-*.json`. The root
`program.json` is the harness's proposed ordinary program: its tail was reused,
but its pointer coordinates were not dispatched in this mode. Do not replay it
as the executed guarded program. Native session results, checks and all captures
are retained. Absolute artifact paths refer to results-local; archived copies
keep the original basenames under each run. `SHA256.json` hashes 92 files;
`final-source` is the final source snapshot, including harness cleanup handling
added after the runs. The README is excluded from that manifest.

Six adapter unit tests plus seven adjacent failure/result tests passed. They
cover changed pixels, moved pointer before press, unblocked button release,
expired guard, no dispatch after refusal and explicit retained source selection.
CI includes the new adapter boundary tests.

## Remaining scope

- There is still a non-atomic interval between capture/check and X11 input. The
  bridge does not freeze the application or prove that every possible race is
  eliminated.
- Only the pointer click is guarded. Text/key operations in the tail are ordinary
  native operations, not semantic field-effect checks or renewed target grants.
- Exact patch equality is not semantic identity. Window translation behavior
  comes from the existing store; arbitrary occlusion/layout changes need repair.
- The explicit focus invalidation refuses; automatic repair and six-task
  cold/reuse/invalidation/repair/reuse acceptance remain untested on this bridge.
- The native input call still uses a fixture binding revision of zero, while
  target checks use live focus/surface/geometry. General source-revision and
  multi-client coordination are not established.

With the predecessor's local dependency setup:

```sh
XAUTHORITY= python3 -m runtime.native_result_self_use --native-artifacts \
  --read-only-continuation --native-handles --probe-guard-focus-change \
  --out NEW_DIRECTORY
```

View that run's full-screen initial image before supplying its request. The
bridge is not included in the portable distribution; the default native path
does not acquire these guards automatically.
