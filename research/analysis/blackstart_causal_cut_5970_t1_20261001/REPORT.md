# Issue #5970 T1 — retained reconnect-trace applicability

## Result

**`HOLD_CAUSAL_EDGE_PROVENANCE_MISSING`**. A retained X11 reconnect trace contains real, relevant recovery state, but not enough explicit cross-source causal metadata to evaluate a nontrivial causal cut after the fact.

The source-frozen archive contains 324 files and 24 formal cases. The four selected positive-policy rows cover disconnect-press and disconnect-release across two repetitions. In all four:

- the exact `observer2.jsonl` bytes agree with the case aggregate;
- the exact Tk `app_events.jsonl` bytes agree with the case aggregate;
- the new observer bootstrap epoch equals the event-stream epoch;
- observer and application records include monotonic timestamps;
- both recorded outcomes are `b` with a neutral terminal key state.

However, neither stream nor the aggregate case records contain explicit causal-parent or send/receive identifiers connecting the bootstrap, observer events, and Tk application events. The observer source uses one X Display connection for the bootstrap keymap query and the subsequent event stream, so that portion is an atomic single-source root/event sequence. The separately recorded Tk event/effect stream has monotonic timestamps but no retained causal edge to the observer stream. Timestamp order is not promoted to a causal message edge.

| Check | Result |
|---|---:|
| Verified archive | SHA-256 `5f153824d677503275f268e2aef9c9971d5f0a3f369c573feaa1a5d10604ad8d`, 36,032 bytes |
| Expanded files / formal rows | 324 / 24 |
| Selected reconnect rows | 4/4 raw-vs-aggregate matches |
| Bootstrap epoch bound to observer epoch | 4/4 |
| Monotonic timestamps in both streams | 4/4 |
| Explicit causal-edge rows | 0/4 |
| Independent audit | PASS, zero errors |

This is not `HOLD_NO_ELIGIBLE_TRACE`: a relevant reconnect/bootstrap state exists. It is not `PASS_TRACE_CUT_APPLICABILITY`: the archived evidence cannot demonstrate how independent streams form a consistent cut. The result identifies instrumentation/provenance as the missing T1 input.

## H / T / D / C / U

- **H:** The retained trace has enough explicit causal-parent/send-receive evidence to reconstruct the cut between bootstrap, observer, and application state.
- **T1:** Verify archive parts and full archive hash from frozen Git blobs; scan the four exact `REBOOTSTRAP_ON_RECONNECT` disconnect rows; independently compare embedded raw event files with aggregates; check epoch binding and edge metadata. No runtime was started.
- **D:** `HOLD_CAUSAL_EDGE_PROVENANCE_MISSING`: relevant state and raw consistency pass, but zero of four rows carries explicit cross-source causal edges. Candidate and independent auditor each ran once; 6/6 construction tests passed.
- **C:** Same-host monotonic times may provide a useful total order for this cooperative fixture, and an atomic observer connection may be sufficient for local key-state bootstrap. A causal-cut layer may add no value for that single-source subproblem.
- **U:** One Xvfb/Tk fixture, two scenarios and two repetitions; no frequency, latency, semantic-truth, authorization, runtime-safety, or product-benefit claim. The T0/T1 evidence does not close the broader #5970 research question.

## Integrity and next measurement implication

Source commit: `7625a3fc99f1da2099dc6e20e67383ee88c7f337`. The archive is reconstructed in memory from the five frozen Git blobs; no archive member is extracted to disk. `FREEZE.json`, `AUDIT_FREEZE.json`, and `SHA256SUMS.txt` preserve the source and one-shot outputs. The full source/raw publication from Issue #4135 is not modified.

For a future prospective multi-source recovery trace to support cut validation, retain source-local sequence plus explicit action/send/receive/causal-parent identifiers across observer and application streams. Do not backfill those edges from timestamp order in this or any historical trace.
