# Primary use of optional native receipt summaries

At source commit `4f8b912912`, the primary assistant used `detail="brief"` through
one persistent Node relay and real native MCP connection on Linux/X11. One new
Calc/Inkscape allocation used seed 991324, 24 stages, explicit 2 ms text pacing,
and owner lifetime tracking. No helper model or sensor was used.

Both saved effects passed independent scoring after the primary visual completion
note: Calc A1=877/A2=107 and SVG x=56, y=50, width=40, height=30, no transform.
Twelve MCP calls returned eight images, five actual input programs and two fresh
observation decisions. Two normal Inkscape results were summarized; the assistant
did not need full retrieval to choose its next action. This is one usability
case, not evidence of general correctness or a default-policy change.

Failures remain in the bundle. A switch to Calc returned needs_review; the new
reviewed image was usable. Saving values completed input but failed post-input
capture with binding changed; full recovery details prohibited further input until
an observation. Confirming XLSX returned BadWindow and a visually stale dialog;
a second observation showed the completed save. No input was replayed. The caller
also incorrectly supplied observe=true once; schema validation rejected it before
publication. The corrected interaction=observe used the still-unused stage.

The first-send-to-finish presentation callback interval was 93,972.619 ms;
8,742.228 ms lay inside send-to-callback intervals. These host timestamps include
orchestration and evidence writing, exclude setup before first send, and do not
measure render onset, pure model inference or actual model tokens/cost. Do not
compare them causally to the earlier full-output case: seed, recovery behavior,
and caller error differ. Human-tempo performance and #57 remain unproven.

The owner reached terminal exit 0 and the relay exited 0. The cleanup receipt
verifies tracked processes only; its owner/descendant verification flags remain
false and are not upgraded by the separate owner status.

## Retained integration evidence

The archive also contains the initial failed local check (missing source-1 test
fixture), corrected check (217 protocol + 97 harness tests), and read-only real
MCP full/brief/full-retrieval checks on five stages of the prior primary two-app
record. Images and full receipts match; request bytes and mtimes were checked
unchanged. No extra GUI allocation was started for those retrieval checks.

The first retrospective projection applied the helper to unsupported tool kinds;
it is retained as exploratory. The corrected `native-brief-retained-02` applies
brief only to submit/resume and gives 54,164 -> 47,307 serialized metadata bytes
across 11 prior replies (12.7% fewer). This is neither token measurement nor live
speed improvement. Full fallback adds a small presentation marker.

`raw.tar.gz` contains 233 files, including all actual transport requests/replies,
images, owner records, saved outputs, primary interpretation notes, host timings,
local checks, and retrospective scripts. `manifest.json` hashes every member.
The host's interactive Node setup remains in the conversation rather than a
standalone replay script. This archive verifies retained evidence, not automatic
reproduction of the model's choices. The retrospective scripts depend on the
previous `native-primary-twoapp-client-01` evidence/local paths.

Run `python -O runtime/results/native-primary-brief-01/verify.py`. It reads the
archive without extraction or action replay and checks hashes, image parity,
request identities, preserved schema failure, normal-only summarization, full
retrieval, primary-review ordering, saved XML effects and terminal records.
