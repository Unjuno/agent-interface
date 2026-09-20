# Primary selection comparison, ABBA

Preregistered PLAN.json fixed source cb7fc0a94, Inkscape, seed991123, max2,
textgap0 and point [600,378]. Four fresh allocations were run serially in the
same primary conversation. The startup PNG SHA256 was identical in all four.
A combined click + six Right + Ctrl+S + finish_after used one submission.
B clicked only, returned an image showing selection at x50, then the primary
issued keyboard-only six Right + Ctrl+S + finish_after from that viewed image.
All images were viewed before authoring subsequent actions. No pacing changed.

| Order | Mode | Saved x | Submit SDK total ms | Images | MCP calls |
|---|---|---:|---:|---:|---:|
| 1 | combined | 62 | 749.007 | 2 | 3 |
| 2 | separated | 62 | 1136.901 | 3 | 4 |
| 3 | separated | 62 | 1223.251 | 3 | 4 |
| 4 | combined | 62 | 688.587 | 2 | 2 |

All kept y50/w40/h30/no transform, passed directional saved-task evaluation and
tracked cleanup, and owners and relays exited 0. The last combined response
already reported terminal exit, so no extra status call was needed; the first
three needed one. Do not attribute that incidental call difference to selection.

The earlier x60 discrepancy did not reproduce. Two examples per condition do
not establish exact-key reliability or a benefit from separating selection.
There is consequently no evidence here to require selection splitting or add
implicit keyboard delays. Keep the existing behavior and preserve the earlier
negative case. B adds one submission/image boundary. Its measured SDK sums
include guarding, execution, feedback, and final cleanup; inter-call reasoning,
image review and orchestration gaps are separate in timing.json. These timings
are descriptive small-sample observations, not a causal overall speed estimate.
No token/cost or model-identity telemetry was available; conversation context
continues across runs. This is not a human baseline or independent/container gate.

Raw requests, replies, images, program/guard receipts, saved files and timing
records are retained under numbered directories. audit.py checks hashes and
protocol/geometry invariants, not screenshot semantics. Manifest excludes itself.
