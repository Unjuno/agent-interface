# MAP01 full-trace occupancy v7: early verified release boundary

## H / T / D / C / U

**H.** A completed hold with a same-program verified empty-input release before its final post-release observation can be over-counted if later captures still extend the positive occupancy lower bound.

**T.** The synthetic boundary (ACK 12 ms, in-hold capture 30 ms, verified empty release 40 ms, later capture 80 ms, post-release capture 90 ms) first failed against v4: it claimed 68 ms confirmed occupancy. V7 caps the lower endpoint at the last in-hold capture before the verified release and the upper endpoint at the release. The candidate and separately implemented raw auditor both pass this synthetic case at 18–29 ms. V7 was then applied once each to the immutable v38/v39 traces and audited once.

**D. `PASS_EARLY_RELEASE_BOUNDARY_SCOPED`.** Independent v7 audit reports source hashes match, raw reconstruction PASS, zero errors for both traces (11/11 v38 and 29/29 v39). Every hold row, every decision row, and all occupancy totals are byte-value equal to v4. Thus this successor corrects a missing boundary without changing the retained historical metrics.

| Trace | Holds | Model-wait occupancy lower–upper (ms) | Difference from v4 |
|---|---:|---:|---|
| v38 | 11 | 3,048.890–4,039.878 | none |
| v39 | 29 | 6,301.200–8,452.733 | none |

**C.** Neither trace contains a completed hold with a verified early-release event. V38 has no `input_released` event; v39 has one, attached to a cancelled program. The synthetic fail-open therefore identifies a construction gap, not a reason to revise these two outputs.

**U.** Two stochastic traces only. Normal key-up remains interval-censored; no task effect, recovery efficacy, performance, causal comparison, human tempo, or MAP01 completion is established.

## Preserved first outcomes

- v4 candidate plus v5 auditor: [`v38.json`](../map01-held-input-occupancy-fulltrace-v4/v38.json), [`v39.json`](../map01-held-input-occupancy-fulltrace-v4/v39.json), [`audit-v5.json`](../map01-held-input-occupancy-fulltrace-v4/audit-v5.json) remain unchanged.
- The v6 successor's two one-shot candidate invocations stopped before output creation due to a helper namespace error. See [`STOP_V6.md`](../map01-held-input-occupancy-fulltrace-v6/STOP_V6.md); v6 source and freeze are preserved.
- V7's frozen source, input hashes, and commands are in [`FREEZE.md`](FREEZE.md). Candidate outputs, independent raw audit, and a compact comparison are [`v38.json`](v38.json), [`v39.json`](v39.json), [`audit-v7.json`](audit-v7.json), and [`verification.json`](verification.json).

## Environment and limits

Deterministic posthoc CPU analysis on macOS arm64 / Python 3.14.5; no live allocation, model, game, input, GUI, or container run. This method correction does not satisfy the broader #59 gate: per-key physical release timestamps, independently useful task feedback, bounded recovery under matched conditions, and the real-time threat-control gate remain open.
