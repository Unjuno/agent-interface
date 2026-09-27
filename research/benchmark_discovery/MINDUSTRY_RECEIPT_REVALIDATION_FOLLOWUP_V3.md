# Mindustry receipt revalidation follow-up v3

This follow-up fills the two live branches left open by the first receipt
revalidation block: a genuinely unavailable current pointer binding and a real
surface resize. It keeps the first block immutable and reuses its unchanged
positive, shared checked-click operation, task, Luna-low prompts/schemas and
fixture.

## Fault-control feasibility

Three no-model live revisions are retained.

1. V1 set focus to the X11 root. The immediate binding was unavailable, but the
   window manager restored Mindustry before the next observation. The probe
   failed and cleanup passed.
2. V2 used a mapped override-redirect InputOnly surface. This held focus long
   enough to record `pointer_binding: null` and restored correctly. A direct
   width change failed because the Mindustry window was maximized.
3. V3 retained the InputOnly focus control and temporarily removed EWMH
   maximization before resizing. Initial geometry `[0,19,1280,781]` changed to
   `[63,70,1216,700]` and restored exactly. Binding also restored exactly.
   It used zero model calls and admitted zero button-downs.

## Formal allocations

Formal v1 stopped before GUI/socket/model because its source verifier duplicated
the `benchmark_discovery/` path. Formal v2 acquired one initial GUI observation,
then its first model process failed before model identity or usage because the
empty workspace directory was missing. Both failures are retained. V3 used a
new preregistration, verified 20 source hashes and the workspace before its
single ordered allocation. No condition was retried.

| Condition | Fresh current evidence | Result | Calls / input | Exchanges / frames | Checked submit | Model reply to evaluation |
|---|---|---|---:|---:|---:|---:|
| binding unavailable | real X11 observation with `pointer_binding: null` | `current_evidence_unavailable`, no authority/point/button, focus restored | 2 / 17,403 | 10 / 7 | 349.214 ms | 1,497.788 ms |
| surface resized | same Mindustry surface, size changed after EWMH unmaximize | `surface_size_changed`, no authority/point/button, geometry/maximization restored | 2 / 17,403 | 10 / 8 | 351.835 ms | 2,030.553 ms |

The follow-up totals four completed model calls, 34,806 input tokens, zero
reported cached subset, 697 output tokens, 471 reasoning tokens, 20 socket
exchanges and 15 exact frames. Parent-observed model time is 39.354 seconds and
31.460 seconds by condition. The short post-model refusal path does not imply an
end-to-end speedup; model service time still dominates these episodes.

The independent audit reconstructs all exact images, durable socket slices, raw
model turns and usage, local revalidation, event ordering, zero button-downs,
verified releases, scorer output, restoration and cleanup. It passes on Windows
and WSL. Together with the retained first-block positive and palette/world/focus
faults, this satisfies Issue #55's finite engineering branch coverage.

These are injected branch checks, not natural fault rates. Exact patches may
over-refuse harmless visual changes, stable change masks do not prove semantic
identity, and the check-to-input interval remains non-atomic at the OS boundary.

## Evidence

- Formal retained attempts: `results/mindustry-receipt-revalidation-followup-01/`
  and `results/mindustry-receipt-revalidation-followup-02/`
- Passing formal block and audit:
  `results/mindustry-receipt-revalidation-followup-03/`
- Retained feasibility:
  `results/mindustry-receipt-fault-controls-01/`,
  `results/mindustry-receipt-fault-controls-02/`,
  `results/mindustry-receipt-fault-controls-03/`
