# #59 — ProgressClock source-epoch identifiability counterexample

## Question

Can the current `ProgressClockV2` distinguish an actually fresh scorer sample from a stale prior-engine-epoch sample when both carry the same state and a newly assigned monotonic `sample_ns`? This addresses the #59 next-gate requirement to bind freshness to producer/update epoch rather than receipt time or unchanged getter tics.

## H/T/D/C/U

- **H:** The current typed sample/API has no producer update epoch, so two upstream histories that differ only in sample provenance but deliver the same `ProgressSample` sequence produce identical scorer events. In particular, a stale prior-epoch kill count can be emitted as positive current-episode progress, and a stale terminal snapshot can be emitted as current terminal state.
- **T:** Import the exact current-main `independent_progress_clock_v2.py` source pinned at commit `5489741c1efa2d25bedf5aa64e60a68fb2f74e3c`. Feed the exact same baseline and changed sample sequence to two labeled provenance histories: current producer epoch versus stale previous producer epoch. Repeat for kill-count increase and terminal no-exit. Inspect API fields and serialized sample for source epoch/update ID. No engine, GUI, model, or input is involved.
- **D:** PASS if (1) both provenance histories produce byte-equivalent event objects for both sample sequences and (2) neither the dataclass nor serialization carries a producer/update epoch. FAIL if the current implementation can distinguish the histories through its provided inputs. The result is limited to the scorer API under the stated upstream-cache possibility.
- **C:** The prior-epoch stale-return condition is an adversarial but plausible upstream behavior, not evidence that ViZDoom actually returns stale values. Other runtime layers may bind/reset sources before constructing a sample.
- **U:** No empirical stale cache, terminal onset, engine tic/update acknowledgment, application effect, controller cadence, gameplay utility, or safety consequence is established.

This is an analytical construction experiment on the current scorer boundary. It does not replace or claim success for the separately proposed one-shot neutral ViZDoom probe. R02 and all prior game runs remain unchanged.
