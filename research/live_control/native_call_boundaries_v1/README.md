# Native call boundaries: where this live session spent time

The retained native-calc-visual-finish-01 relay trace spans 109.085167002 seconds
from SDK entry of native_start through return of native_status. Summed SDK calls
occupy 4.674080220 seconds, including 2.984468182 seconds of startup. The six
between-call intervals total 104.411086782 seconds (about 95.7% of that span).
The integer nanosecond partition sums exactly before conversion to milliseconds.

These intervals include primary-assistant deliberation/image review, outer tool
invocations, response-file reads, commentary and orchestration. They are NOT a
measurement of model inference time alone. The trace does not identify when the
host rendered each image or when it became model-visible. Startup before the
first SDK call and relay shutdown after the last return are outside the span.

Within the two action calls, feedback occupied 48.421242 ms and 0.835411 ms; the
configured 2000 ms maximum was not consumed. Input-free observation bodies took
112.644204 ms and 62.570167 ms; their complete SDK calls took 332.232887 ms and
179.850402 ms. Nested phases must not be added to SDK totals a second time.

This changes the optimization priority for this observed workflow: investigate
the host-to-model-to-tool path before attributing the slow visible tempo to a
two-second feedback wait or tuning small backend intervals. A permanently
connected relay already exists, but the primary assistant still sends requests
through a shell tool and reads the response JSONL through another tool to forward
images. This is not yet a directly registered model-callable native MCP path.
Reducing those steps is a candidate, not measured savings; real model-visible
boundaries remain the gap described in issue #3370.

Reproduce with:

```sh
python research/live_control/native_trace_timing_v1.py runtime/results/native-calc-visual-finish-01/responses.jsonl
```

calc-visual-finish.json retains the source trace SHA256 and all per-call/gap
values. The reader rejects reversed/overlapping call timestamps and nested phases
outside their enclosing call, rather than adding historical resumed work into a
new call. It operates on returned sequential same-clock traces only. It does not
claim task correctness; that is covered by the original artifact audit and
primary image review. Frozen run files are unchanged.

There is no same-model matched baseline, timing distribution, token/cost evidence
or human comparison here. The result identifies a measured end-to-end gap in one
session, not a general performance result or evidence for autonomous local agents.
