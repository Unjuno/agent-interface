# Public MCP transfer of the Inkscape selection workflow

Source: `961f14b836e549ca5f6cfb6bf3ef4b470e91b1b5`.
Disposition: **WSL primary functional transfer; formal container gate remains open.**

The primary agent used public stdio MCP through the SDK, viewed the initial
Inkscape image, clicked the red rectangle, inspected the returned selection
handles and X=50/Y=50/W=40/H=30, then chose six Right chords, a 50-ms wait,
Ctrl+S, a 50-ms wait, capture and release. The action image showed X=62 and
Document saved. Independent XML readback confirmed x=62/y=50/w=40/h=30 and no
transform. Both actions reported completed and input_release_verified=true.

The harness additionally required a final explicit observation: it still showed
X=62, while the transient saved status had reverted to the normal selection
status. This extra observation was confirmation overhead; the second action
image was already sufficient for the primary visual decision. There were two
input dispatches and two explicit observations, with no replay. Source/binding
values are caller assertions; each chosen dispatch received a 10-second lease
immediately before invocation. The server did not issue source authority.

## Preserved startup failures

- Attempt 1: installed Inkscape rejected --new-window. No MCP/input calls.
- Attempt 2: --app-id-tag launched a process, but no mapped matching X11 window
  was discovered in 10 seconds. No MCP/input calls. Its display destination was
  not established; do not claim this attempt reached the private X11 screen.
- Attempt 3: explicitly set GDK_BACKEND=x11 and decode byte-valued WM names.
  Used a fresh app-id tag and fresh output. The private X11 target was observed
  and controlled successfully. Because two construction changes were made, this
  does not isolate the cause of attempt 2's discovery failure.

Each preceding attempt was terminal before the next started. Attempt 3 tracked
Xvfb/Openbox/Inkscape PIDs 33876/33880/33881 exited 0/0/-15. The harness exited 0.
All attempts retain process logs and cleanup records; descendant cleanup remains
unverified. The owned file is disposable; no existing document was edited.

## Scope

This transfers the explicit selection-before-keyboard workflow from #3632's
native research path to the public MCP entry point in one real application.
The 50-ms waits are explicit caller choices, not proven optimal/default values.
No causal speed benefit, model-token/cost saving, registered host presentation,
cross-app reliability, or general task completion is claimed. No sensor or
public runtime change is introduced. Keep as draft until applicable formal gates.

The archive contains all 46 files from all three attempts. manifest.json and
archive.json record file hashes/lengths and archive identity. Every archived
entry was checked. Preserve all three attempts; do not rerun them in place.

## H/T/D/C/U

- **H:** The primary can select the rectangle, make the requested six-Right
  transfer and save through public MCP; the explicit final observation adds
  confirmation but no new information beyond action 2's visible saved state.
- **T:** One WSL/Xvfb Inkscape session through SDK stdio, with three sequential
  startup attempts. Attempt 3 used explicit X11 backend and byte-valued WM-name
  decoding; it does not isolate which change resolved attempt 2's discovery
  failure. No input replay.
- **D:** The archived attempt-3 SVG verifies `x=62`, `y=50`, `width=40`,
  `height=30`; action receipts report completed and input release verified.
  The archive digest matches and all 46 manifest entries match exact sizes and
  hashes. Tracked cleanup is retained; descendants remain unverified.
- **C:** One WSL/Xvfb functional-use case with explicit 50-ms waits and an extra
  observation. Source/binding labels and leases are caller supplied. No
  matched timing comparison, host registration, or model acknowledgement.
- **U:** The formal container/adoption gate remains open. No default-delay,
  latency, cost, broad GUI reliability, or general task-completion claim follows
  from this single scoped transfer. Keep the formal gate separate from this
  retained WSL evidence.
