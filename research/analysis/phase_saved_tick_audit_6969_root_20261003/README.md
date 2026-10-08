# Supplementary saved-only tick audit — #6969

At base `effc43f8bd11f20f83c3410101c04f31c0c353f7`, a separately written
integer-tick simulator reconstructed all **147/147** saved rows, including the
zero-delay same-tick and decision-before-expiry/effect-after-expiry boundaries.
Disposition: **PASS_SAVED_FINITE_AUDIT**. This supports retaining the finite
method result; live transfer remains **HOLD**. Refs #6969 and #6957.

The original candidate, legacy diagnostic and formal auditor were not executed.
No original source, raw, receipt or historical result was changed. The new
checker imports only the standard library and reads the six prospectively
hashed source/evidence files in `PLAN.json`. Their bytes were checked against
the pinned Git blobs before execution. The reconstruction advances time one
integer tick at a time rather than calling the candidate or its set oracle.

## Executed check

From this directory, the recorded command was:

```sh
python -B check_saved.py --study ../exogenous_phase_6803_derived_capture_a05_20261003_3cbf --plan PLAN.json --out RESULT.json
```

One invocation, exit 0; stdout/stderr and exit are retained. `RESULT.json`
contains actual UTC start/end, CPython 3.12.14/Linux identity, every control path
and outcome. Output creation is exclusive; a deliberate future reproduction
must use a new output filename. The original formal allocations remain consumed.

| Check | Result |
| --- | --- |
| Original rows versus independent tick model | 147/147 exact typed matches |
| One changed value at every scalar output leaf | 2,058/2,058 effective and rejected |
| Dropped, duplicated, reversed rows; extra field | 4/4 effective and rejected |
| Integer 0/1 replaced with equal-valued boolean | 8/8 effective and rejected |
| Total copied-evidence controls | 2,070/2,070 effective and rejected |

Counts independently reconstructed: 76 eligible effects **in the model**, 22
not acquired, 41 delivered without decision, 2 acquired without timely delivery,
2 decision without effect, 3 UNKNOWN and 1 NOT_APPLICABLE. These are authored
finite cells, not sampled success rates. Simulated tokens are not application
effect receipts.

The value-changing controls check exact comparison and traversal coverage.
Their rejection is largely a property of typed canonical equality, not proof
that the semantic oracle is correct. The separate tick reconstruction provides
the semantic cross-check; it can still share a mistaken contract interpretation.
No theorem about all possible corruptions or inputs is asserted.

## Prospective decision and limitations

H/T/D/C/U, input Git blobs/SHA-256, checker hash and command were fixed in
`PLAN.json` before execution. Acceptance required the exact 147-row match and
all generated controls effective/rejected. No threshold was changed after
observing the result. `AUDIT.json` separately checks the saved result's coverage,
typed original/replacement values, counts and hashes without importing either
checker or original study implementation.

This is a supplementary analytical saved-evidence check on the local Linux CPU,
not a new container-backed formal allocation, live experiment, performance
measurement or adoption vote. No GUI, native input, GPU, model, Docker operation
or shared resource allocation was used. It does not establish physical capture
timing, cancellation/release safety, actual task benefit, economics, #57/#59
completion or the whole #6957 checkpoint. No new scientific Issue is needed.

The next useful research decision remains transfer to an independently scored
live boundary under its separately granted allocation, rather than another
repeat of these finite cells. Publication is an additive reviewable PR; main
integration requires the FINAL-v5 nonauthor quorum and current-tree gates.

Worker: actual API agent `/root`, FINAL-v5. Common deadline and other workers'
capacity were not supplied; no 48-hour supervisor was configured. No pending
native effects or input/resource locks belong to this check.
