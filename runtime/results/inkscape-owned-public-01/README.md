# Primary Inkscape admission through shared owned public dispatch

The primary assistant used source df2e5c6f3ca7288f5a054195f8a746d1ab4ead54 in
Ubuntu directly, with one fresh private Xvfb/Openbox/Inkscape 1.2.2 allocation.
The new `MCPSessionOwner.dispatch` was used for actual pointer and keyboard input,
without a manual dispatch-attempt flag. No subagent, sensor, queue or input retry
was used. This extends the prior owner's mechanics probe to a real saved-file
application task, not a matched performance comparison.

## Task and outcome

The task was to create two distinct non-overlapping rectangles wholly inside an
empty 400x240 SVG page and save it. The initial selected reply image showed the
full page. The primary selected two new drags from that image: (320,280)->(430,340)
and (490,370)->(620,440). One 15-operation public batch kept the existing strong
baseline semantics: focus, rectangle tool, both complete drags, explicit waits,
observation and release. The primary saw both shapes inside the page, then chose
a separate 5-operation save batch. Its image showed the same shapes, removed
unsaved title marker and Document saved status. A fourth command closed the owner.
No extra observation, replay or repair was required.

All three exact selected original PNG blocks are attributed to the primary
source records, with matching hashes and explicit subsequent review declarations.
The two input programs completed with verified neutral releases; close made the
same-owner release and closed the connection. The original tool handle 23417
ended with exit 0. Inkscape exited -15 under caller cleanup; Openbox and Xvfb exited
0. Independent inspection occurred only after every owned process was terminal.
The saved SVG contains exactly two positive, untransformed, non-overlapping
rectangles within its page, at (31.525423,36.610168), size111.86441x61.016949, and
(204.40678,128.13559), size132.20338x71.18644. Saved SVG SHA256 is
90d605571886c3e07464c808c3f89669987bd939217579baa761706fa0e22403.
This proves that scoped predicate, not arbitrary precision or broad reliability.

## Time, token and failure accounting

`report.json` retains separate host and primary declaration boundaries. Owner
acceptance to response readiness was52.537ms observe,240.477ms draw,132.593ms save,
and0.808ms close; these include their explicit waits and image projection. Helper
publish to reply read was81.794/246.663/143.039/20.391ms. Reply read to later primary
review declaration was23.824/17.682/16.020s for the three images. Those intervals
include orchestration and reasoning; they are not measured internal model
inference, image ingestion, first useful feedback or independent semantic
completion. Host subsecond responses do not establish human-tempo operation.

Actual whole-context model usage is retained in `primary-usage.json`, projected
from34 selected source records. Observed context alias is gpt-6.1-sol, effort
medium; exact provider build and billing remain unavailable.

| Window | Input | Cached input (subset) | Uncached input | Output | Reasoning (subset of output) | Total |
|---|---:|---:|---:|---:|---:|---:|
| Preparation through terminal audit |1,395,494|1,366,144|29,350|7,818|1,746|1,403,312|
| Allocation setup through owner terminal |753,461|736,768|16,693|5,568|597|759,029|
| Joint remainder outside owner window |642,033|629,376|12,657|2,250|1,149|644,283|

The first two windows overlap: never sum them. The latter two partitions sum to
the first. Whole-context response usage is not an isolated image/tool charge.
Branch preparation and an initial functions-store serialization failure are
included; the failure occurred before command publication and did not emit input.
The corrected adapter then forwarded exact retained images, without retrying an
owner command. Planning before branch creation and later publication are excluded,
not zero. Cached counters are subsets, and no monetary cost is inferred.

## Scope and reproduction

`PLAN.md` and the hashes in `FROZEN.json` were fixed before allocation and remain
unchanged. `owner.py` is a caller fixture using the pinned repository directly,
not a new production controller or fair public-MCP transport comparator. It needs
Xvfb, Openbox, wmctrl, Inkscape and the provisioned Python environment. A fresh
reproduction can invoke it from the repository root with `PYTHONPATH=.`; it must
allocate a new case directory. The retained owner intentionally refuses an
existing case. Do not transplant the coordinates/source/lease into another run.
Caller leases here are explicit2-second deadlines issued immediately before
publication; current source and binding remain explicit caller assertions. Fixed
waits do not acknowledge redraw. Native initialization/configuration is fixture
preparation; application shapes and save came from primary public dispatch.

`python -O verify.py` checks frozen bytes, original image identity/review
attribution, completed input releases, cleanup records and independently parses
the saved SVG geometry. The terminal audit additionally confirmed owned PIDs were
absent and original tool handle terminal. The verifier does not prove model
perception, timing causality or generic GUI reliability.

Disposition: SCOPED_SECOND_APPLICATION_ADMISSION. Promote the documented owner
usage based on this task; retain no new defaults or automatic path selection.
Historical `public-inkscape-batch-01` already provided a strong batched route;
its different build, lease, task geometry, host and model context preclude a
matched speed/token comparison. Four calls here versus its five (including an
extra retained-result lookup) is not a fair roundtrip improvement. No generic
latency, memory, cost, token reduction or product-completion claim is made.
