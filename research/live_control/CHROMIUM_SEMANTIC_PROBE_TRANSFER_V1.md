# Chromium semantic-probe transfer

## Result

The no-authority pre-artifact semantic probe now works for one deterministic
ordinary-browser completion predicate, in addition to the earlier Inkscape
selection predicate. This is a cross-domain feasibility result on Linux/X11,
not a general GUI or human-tempo result.

The probe checks an exact bounded RGB crop for the visible `Submission
received` heading. It runs on the losslessly reconstructed frame before PNG
publication, emits a provisional action-scoped result, grants no input
authority, and later reconciles the scored frame digest to the durable PNG.
Four historical success frames matched the crop before the live allocation;
an unsubmitted form and an `about:blank` frame did not.

## Retained v1 failure

The seed206 allocation performed the intended task correctly but failed its
formal gate. The blank negative was rejected, the submitted positive was
detected, the server saved exactly `t000206`, and every consumed probe
independently rescored and reconciled. Useful feedback reached the client in
263.414ms, 23.087ms before its PNG was ready and 140.319ms before terminal.

The frozen gate incorrectly required the total number of backend
reconciliations to equal the number of probes consumed by the client. The
client stopped correctly at its first success, while the program produced one
later observation: four reconciliations were generated and three probes were
consumed. This sole formal failure is retained without retry in
`results/chromium-semantic-probe-transfer-live-01`.

## Repaired v2 allocation

V2 changed only that cardinality rule and used fresh seed207. It requires:

- every generated reconciliation to match its durable exact frame;
- every client-consumed probe to have a corresponding reconciliation;
- the blank negative to reject and the submitted positive to accept;
- the independent saved value to equal the requested token;
- every program to terminate with verified empty input;
- zero model calls and zero retries.

The first v2 allocation passed all 15 formal checks and the independent audit.

| Measurement | Result |
|---|---:|
| Blank admission to negative feedback | 42.098ms |
| Submit admission to first feedback | 146.995ms |
| Submit admission to useful semantic feedback | 286.471ms |
| Useful probe compute | 2.608ms |
| Useful probe before PNG ready | 24.767ms |
| Useful client result before terminal | 156.657ms |
| Positive client exchanges | 2 |

The retained v2 artifact contains 29 files and 675,988 bytes before its
retention receipt. Windows and WSL audits both pass. The result covers one
scripted Chromium fixture, one exact completion predicate, and one fresh seed.
It does not establish a reliability rate, model or token savings, a causal
latency comparison, portability, or human-speed interaction.

## Next decision

The shared registry can now host two typed predicates with different semantics.
The next useful refinement is to replace hard-coded screen coordinates and the
fixture-specific exact crop with a target-relative predicate bound to current
surface geometry, then test invalidation under translation or resize. That
tests whether the semantic feedback contract composes with the existing target
handle and freshness machinery instead of adding another fixed-layout fast
path.
