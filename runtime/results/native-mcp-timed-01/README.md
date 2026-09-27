# Primary MCP use with nested SDK timing

The primary assistant viewed the actual MCP-returned initial image and public
goal for Inkscape seed 991118, then authored the existing click/wait/18 right
chords/wait/save/finish_after decision. It viewed the final returned image.
One persistent SDK connection performed startup, submission and terminal status;
there was no autonomous action selection, sensor work or Docker operation.

Independent SVG inspection finds x=86, y=50, width=40, height=30 and no transform.
One program emitted 43 operations, input release was verified empty, feedback
matched, cleanup reported completed and harness PID 17128 exited with code 0.
The SDK bridge exec session 95780 also returned 0. This is one successful case,
not a reliability rate or crash-recovery result.

The driver records monotonic timestamps immediately around SDK call_tool,
before writing results or decoding image blocks to files:

| Boundary | Duration |
| --- | ---: |
| native_start SDK call, including app setup | 4674.187 ms |
| native_submit SDK call | 984.206 ms |
| nested exchange entry to return | 964.031 ms |
| SDK entry to nested exchange entry | 17.688 ms |
| nested exchange return to SDK return | 2.487 ms |
| native_status SDK call | 3.744 ms |

The two outer portions sum to 20.175 ms. They combine transport, dispatch,
ownership checks, content encoding and other work; they are not pure network
latency. The bridge then saves/decodes images and the assistant views them with
a separate tool. Host presentation, model interpretation, first useful feedback
and semantic-completion awareness are not measured by these SDK timestamps.
No causal comparison with the prior 1133.463 ms internal run is justified:
these are separate sequential trials with different seeds and uncontrolled load.
Model tokens, cost and human baseline remain unmeasured.

Run `python3 runtime/results/native-mcp-timed-01/audit.py` from the repository
root. It verifies 50 manifest files, exact extracted MCP image bytes, saved
geometry, request/reply digest, release, terminal owner and nested timing sums.
`timing.py` additionally partitions the internal harness timestamps. PLAN.md
was written before allocation; client.py is the exact driver. The manifest
covers the original archive entries, not this README or the later audit script.
No runtime production source changed during this trial.
