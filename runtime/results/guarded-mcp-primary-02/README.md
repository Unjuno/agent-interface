# Public guarded MCP primary use

Decision: **integrate as an explicit opt-in mode**, with existing defaults and
pacing unchanged. This is a scoped usability/integration result, not a general
performance benchmark.

The primary assistant used the public `guarded-x11` MCP mode against a Chromium
fixture in WSL/Xvfb, through the real Python MCP SDK and persistent Node relay.
Runtime archive source: `2998586f5497e12940fe89992a398a2098298887`.
Seed: 991329. The private process set up the initial page and later evaluated
submission history; all task interactions were chosen and sent by the primary
assistant. No helper model, DOM automation, task-selection loop or sensor was used.

## Observed result

- Six independently recorded values exactly match the six goal tokens, each
  submitted once, with no duplicates, missing tasks or unexpected submissions.
- A bounded old-alias control on the changed fourth-task layout returned MISSING
  before admission, with `input_dispatched=false`. The assistant explicitly
  grounded two new aliases from its returned image and continued.
- 32 MCP calls: 22 completed inputs (12 field/Save operations and 10 navigation
  operations), one refused input, five mints, one initial observation, two
  retained-result reads and one close. 25 responses contained images.
- 20 explicit review declarations bind their own retained response/call/source
  and image hashes. The assistant viewed the entered text before each Save and
  the URL before each navigation confirmation. The declarations record caller
  review, not machine-verified visual understanding. See the timing limitation
  below and `AUDIT_NOTES.md`.
- Completed input releases and final close report verified empty key/button
  sets. A result read after close returns the identical final image without new
  input or observation. Its embedded session snapshot remains historical.
- Relay and fixture runner both exited 0. Three tracked GUI children terminated
  with codes 0, 1, 0; no claim that all helpers exited successfully. Cleanup
  records preserve those exact statuses.

## What this does not establish

The preceding interrupted trial remains unchanged at
`../guarded-mcp-primary-interrupted-01`; it includes a navigation text-drop
failure and erroneous first-source attribution in review notes. This new trial
uses an explicit retained-reply review helper. Its URL procedure inserts bounded
100 ms waits and checks the address text before Enter. This was not a matched
comparison and does not justify changing default pacing or claiming the failure
cannot recur.

The 32 host send-to-return intervals total 8,358.3 ms, median 310.5 ms. First
host send through final Save response was 223,553.6 ms, including primary
reasoning and tool orchestration. These boundaries do not measure first useful
model-visible feedback, model waiting, or independent semantic-completion delay.
Linux monotonic and Windows host clocks are separate. Actual model input tokens,
image token accounting and costs are unavailable. No speedup, token reduction,
human-tempo or general desktop completion claim follows.

Review files were awaited before sending subsequent actions in the primary
conversation. Filesystem mtimes for three review/Save-request pairs are equal,
so the bundle alone cannot establish their strict order. The verifier checks
coarse non-later consistency only. Future timing studies need an ordered host
event stream; review declarations also remain declarations, not proof of reading.

## Verification and reproduction scope

Run `python3 -O verify.py`. It reads `raw.tar.gz` without extraction and checks
531 file hashes, transport identities, submitted values against goals, release
reports, source/image-bound reviews, refusal, retained image equality, archive
identity, close and terminal process records. It does not rely solely on an
oracle success flag or on Python assertions.

The archive includes the exact portable runtime, build manifest, private setup
script, goal/allocation, all requests/replies and server captures, independent
history, host timings, review declarations, cleanup, and current contract logs.
The setup script's local paths and seed are explicit; allocate a fresh output
and display for another run. Primary model decisions are interactive and not
replaced with a scripted task policy. Original closed aliases cannot be resumed.

The public MCP contract tests now include successful explicit window review and
invalid mint geometry; the integration suite passed 240 protocol and 106 harness
tests. The Node review/relay suite passed eight tests in the preceding turn.
Contract tests are separate from the six-task live result.