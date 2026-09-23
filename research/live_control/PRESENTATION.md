# Optional compact presentation with full local archives

`interactive_v10.py --presentation compact` applies `presentation.py` only to
the stdout presentation lane. `events.jsonl` and all image/packet artifacts retain
the complete source trace. The default remains `--presentation full`.

Compact mode suppresses per-key admission and step-start/end notifications.
Outside explicit settle steps every observation is forwarded. Inside a settle
step it forwards the first observation, changes in window context/focus, every
ambiguous-focus sample, and the latest observation before the settle result or
terminal event (including failure/expiry). Other event types, including unknown
ones, are forwarded. This does not add event detection or classify image content.

This is **lossy presentation**, not a lossless codec. A transient visual warning
inside a settle interval with unchanged window/focus metadata can be omitted
from stdout. It remains in local archives, but is not guaranteed to reach the
planner. The earlier retained-critical-event work is not integrated into this
CLI. Compact mode therefore stays explicit and experimental; broad claims of
preserving all decision-relevant information are unsupported.

## Actual assistant pair and same-trace replay

The assistant performed two fresh Calc sessions with the same seed 960101,
same runtime source, same cell values, and the same two action programs. Compact
ran first, full second. In each case the assistant inspected the initial screen,
painted save-format dialog and final worksheet. Both independently saved
A1/A2=[532,532]. Both programs in each arm and owner shutdown verified release.
Twenty-nine packet frames audited exactly across the pair.

| Source trace | Raw records | Compact records | Raw JSON bytes | Compact JSON bytes | Same-trace reduction |
|---|---:|---:|---:|---:|---:|
| presentation-assistant-01, compact live | 52 | 22 | 16,253 | 10,338 | 36.39% |
| presentation-assistant-02, full live | 53 | 22 | 16,990 | 10,371 | 38.96% |
| quiet-assistant-01, earlier full trial replay | 53 | 22 | 16,789 | 10,230 | 39.07% |

The replay holds each trace fixed, isolating serialized-output selection from
GUI timing variation. Bytes are UTF-8 JSON lines, including metadata; they are
not text/image tokens, image payload savings, or an end-to-end speed measure.
`delivered.jsonl` is written before the stdout print attempt. It records selected
output, not transport acknowledgement or proof of model receipt. PTY escaping,
command echo and tool truncation are not included in these byte counts.

First runtime acceptance to independent evaluation was 19.43 s compact and
28.51 s full. This includes assistant inspection and tool boundaries, but the
pair is exploratory, ordered, shares conversation learning, and uses unequal
tool-output truncation limits. It is **not causal speedup evidence**. Both arms
still required two accepted programs. Model identity/settings are inherited from
the current task, not independently instrumented. Actual token accounting,
response-generation timestamps and a counterbalanced matched study remain open.

Four projection tests passed: final flush without duplicate delivery, transient
focus-change forwarding, unknown event/non-settle preservation, and final-image
flush on failure. Audits reproduce exact selected event order from raw traces,
check retained terminal/settle/focus-mismatch events, and independently verify
saved workbooks and source/image hashes. Existing source timestamps remain
observation timestamps when a record is delivered later; they are not send times.

## Reproduce

From this directory in the documented Ubuntu/WSL environment:

```sh
python3 -m unittest test_presentation -v
python3 audit_owner_sessions.py results/presentation-assistant-01 results/presentation-assistant-02
python3 audit_presentation.py results/presentation-assistant-01 results/presentation-assistant-02 results/quiet-assistant-01
python3 interactive_v10.py --app calc --seed 960201 --presentation compact --out ../../results-local/compact-new
```

Next: connect explicit critical-event retention before broader adoption, record
actual send/receive and planner timing, and counterbalance fresh task pairs. Keep
presentation selection, byte compression and eliminating planner decisions as
separate changes. Compact mode does not solve blocking file/stdout I/O.
