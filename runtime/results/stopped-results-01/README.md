# Explicit historical result inspection after STOP

Local integration candidate; parent PR #6077 remains pending, not adopted on main.
Source frozen before one live allocation at
5e503cdfc9e3a441cf330e840c35164f72f0a466; archive SHA256
d90c4cb207e31e1f72f68d41dd2ea9c112948f40409baccd210f591be270d93b.
Seed 1001071, Save acknowledgment delay 3000 ms, explicit title budget 1000 ms.

`resultsAfterStop(callId)` fixes one explicit `interface_results` request to a
32-character lowercase hex ID, full historical metadata, no image. It uses the
same instrumented host/server. No list, input, fresh capture, projection, polling,
replay, remint, reconnect or authority recovery is added. Original STOP persists
through successful or failed reads. Ordinary call's extra arguments cannot expose
the private stopped-read entry. Both guarded-local and direct-post are supported.

The primary actually used the frozen packaged Node caller/host and packaged
Python relay/public MCP server against native X11 in Ubuntu/WSL. Primary reviewed
original initial, Pending and later Saved images. After Pending stopped ordinary
calls, it read native execution/guard details and selected historical cue fields,
recorded text acknowledgment, explicitly obtained a later screen and closed.
It did not read every JSON field semantically; original full responses are retained.

After all owned processes exited, independent application records showed one
Save of t1001071 and one Saved acknowledgment 3001.314 ms later. Six public
requests, three primary images, seven captures and one native input program.
Retrieval added zero native operation reports and zero image blocks; the later
explicit observation advanced source sequence 6 to 7. Historical input result,
all guard checks, feedback, source/observation, session and call ID remained equal.

The retrieval's framework isError flag is false, while its historical status
stays needs_review and its cue stays pending. The original input isError was
true. Reading successfully is not successful input/completion; STOP was unchanged.
Historical image_status can still say image, but include_image=false emits no
image content and performs no capture. These distinct facts are retained.

The later screenshot was captured 41302.769 ms after application acknowledgment;
the application clock continued during primary inspection. This proves useful
historical inspectability without duplicate action, not improved reaction speed,
semantic-awareness latency, human tempo, or reduced tokens/cost. Usage and billing
are unattributed. There is no comparative baseline. No live second-input attempt
was made; explicit input blocking/no fourth-argument bypass are unit-tested.

Initial missing-method RED is retained. The full selected host suite passed
156 tests (existing relay timeline and all host test files, including the new
stopped-result cases). The preceding stopped-observe candidate's local shared
native CI passed 374 protocol/176 harness tests; that older result is not a new
run for this commit. Python production code is unchanged here.

`python3 verify.py` and `python3 -O verify.py` pass: exact host metadata/error flags,
primary PNG bytes/hashes, full historical field equality, no retrieval image,
same session, exact native counts, app/capture ordering and terminal cleanup.
Seven in-memory counterexamples must fail: cleared STOP, altered cue/input,
operation invocation, image resend, extra request and duplicate Save. This finite
audit does not replay the allocation or establish universal safety.

Decision: retain helper as local integration candidate, HOLD_EFFICIENCY. Preserve
old frozen studies and parent queued CI; batch publication after parent resolves.
