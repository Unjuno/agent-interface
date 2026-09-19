# Renewable cover during model inference

The frozen Astra hero attempt exposed a shared lifetime defect: a model call can
outlive the accepted ten-second local cover program. Seven of 13 calls had an
uncovered tail, totaling 9.771 seconds with a 3.765-second maximum. The game
continued to advance, but the stronger claim that local control remained active
throughout inference was false.

Controller v18 moves the model call to a worker thread. The main controller
continues consuming exact runtime events. If cover completes while inference is
pending, it submits the same bounded policy under a new ID, using the latest
observation sequence and a new validity deadline. Each program still completes
or cancels independently and verifies release. There is no implicit queue,
unbounded hold, or extension of stale authority.

## Development probe

A four-decision Astra-low normal MAP01 probe used six cover programs. Two model
calls exceeded their first ten-second cover and caused two renewals. Terminal to
fresh admission measured 21.436 ms and 20.710 ms. Across all four model windows,
the audit found three uncovered segments: the two renewal gaps and a 12.042 ms
tail where the model completed almost simultaneously with cover. Total uncovered
model time was 54.187 ms and the maximum was 21.436 ms.

The player remained alive, but the run was deliberately scored unfinished after
four decisions. This is a lifetime-mechanism result, not evidence of better
gameplay or a MAP01 clear. It reduces seconds-scale uncovered tails to measured
tens of milliseconds in this probe. A small release/readmit gap remains.

The next layer should let the model author a compact cover policy for the next
inference interval, so renewal preserves resource-aware fire and evasive movement
instead of repeating a controller heuristic. A later frozen hero attempt must
be versioned separately; the failed v1 allocation is never rerun.

Run the repository-backed audit with:

```sh
python research/doom/audit_map01_cover_renewal_v1.py
```
