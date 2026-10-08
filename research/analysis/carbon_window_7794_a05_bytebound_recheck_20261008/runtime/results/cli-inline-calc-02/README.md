# Primary CLI use with image and metadata in one host response

The primary assistant completed a fresh isolated WSL Calc task, entering 6 and
23 with formula `=B2*A2` and saving 138. All four CLI responses were parsed by the
host tool, which emitted every metadata field and the response's PNG together.
No separate `view_image` call or metadata projection was used. This demonstrates
live use of the retained-data forwarding feasibility in #3544.

The sequence was initial observation, visible Tip closure, table entry/save,
then one explicit final observation. The entry/save image still showed Saving;
the primary confirmed 6/23/138 only from the final image. The saved FODS contains
`of:=[.B2]*[.A2]` and numeric value 138. Both dispatches report completed with
verified input release. No input was replayed. The earlier initial-image extra
observation was unnecessary here because the Tip was already drawn; this is not
evidence that the forwarding method improved redraw or reduced task latency.

## Host integration pattern

Use the existing CLI `--review --compact --report-refs` response. After obtaining
the complete stdout JSON, separate only its `image` field. In a host with the
`text` and `image` output helpers used by this task:

```javascript
const response = JSON.parse(stdout); // Reject partial/truncated JSON.
const { image: png, ...metadata } = response;
text(metadata);                     // Preserve every non-image field.
if (png) image(`data:${png.mimeType};base64,${png.data}`);
```

These are host output helpers, not a new runtime API. This run used a bounded
local `deliver.py` wrapper to submit each explicit primary decision once and
await its saved response. A pending timeout requires reading the same label
without resubmission. This is not a promoted queue, general scheduler, direct
registered MCP connection or automatic action-recovery mechanism. Large stdout
responses remain subject to host limits. The primary saw the complete response
in this run; no input-token/cost or matched transport advantage was measured.

## Evidence and limits

The 73-file `evidence.tar.gz` includes exact requests/reports, stdout PNGs,
decisions, helper/harness, initial/final document, cleanup, the pinned candidate,
and the preceding `cli-inline-calc-01` storage STOP under a separate prefix.
The executable SHA-256 is
`aa9024a5eea4384bdbba349b907f9f2a279ca2d041e50418a7820e778591aae0`,
from source `2dff80852292cc82fd5c23a449c8244bea94bc25`.

Run `python verify.py` to read the archive without extracting or executing its
contents. It checks hashes, four request/report pairs, PNG equality, recorded
release, saved formula/value, and recorded cleanup. WSL returned
`PASS_RETAINED_CLI_RECORD_CONSISTENCY`. It does not independently prove host
rendering, model interpretation or live cleanup; those are the recorded primary
observations. Historical harness paths reference the original local allocation.
Private-test leases were explicitly refreshed after primary decisions.

The predecessor stopped before input during storage I/O failure. Its empty or
partial diagnostic files remain unchanged; see the [STOP account](https://github.com/Unjuno/agent-interface/issues/3544#issuecomment-5751638461).
An attempted launch of this successor first failed in WSL process initialization,
before its `started` marker existed. After a successful WSL health check, this
allocation executed once. No Docker restart/repair was performed by this task.
Owner exited 0; tracked Calc/Openbox/Xvfb cleanup returned 255/0/0 with captured
member paths absent. Full descendant closure and graceful application close are
not established. Storage recovery and differing initial readiness prevent a
causal elapsed-time comparison with previous runs.
