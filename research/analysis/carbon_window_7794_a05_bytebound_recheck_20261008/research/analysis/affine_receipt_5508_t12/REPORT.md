# Issue #5508 T12 construction pilot — cross-store crash recovery

## Disposition

**Exploratory construction PASS, not confirmatory.** The runner unexpectedly executed the full seven-case matrix during a step intended as a small smoke check. It ran once on host Python 3.14, before source hashes were frozen or a GitHub preregistration comment was posted. Do not relabel it as a formal allocation and do not rerun the same matrix.

The stdout returned by that invocation is preserved in `raw/construction-pilot.jsonl`, transcribed from the execution output after the run (it was not redirected to a file at execution time). The seven pairs of file-backed SQLite stores were copied from that invocation into `raw/db/`. This provenance limitation is part of the retained result.

## What the pilot exercised

Each case used a real child process and two separate local SQLite databases: one for affine receipt consumption and one for the simulated external effect. The parent killed the child with SIGKILL before consume, after receipt commit, or after effect commit but before high-level observation. A separate observer process read the effect store. Two scenarios re-presented an already consumed receipt.

| Trace | Recovered state | Observation |
|---|---|---|
| kill before consume | `NOT_STARTED` | receipt remains AVAILABLE; no effect |
| kill after consume, before effect | `UNKNOWN` | retry rejected; no effect |
| kill after effect, before observation | `CONFIRMED_SAME_ATTEMPT` | matching attempt/delivery and target; retry rejected; one effect |
| wrong target | `UNKNOWN` | delivery lineage matches, semantic target does not |
| foreign attempt/delivery | `UNKNOWN` | target looks correct, but effect lineage does not match receipt |
| observer unavailable | `UNKNOWN` | matching effect exists but no independent observation |
| normal valid completion | `CONFIRMED_SAME_ATTEMPT` | exact lineage and target observed |

An independent auditor reopened all 14 retained databases and reconstructed all seven states: `NOT_STARTED=1`, `UNKNOWN=4`, `CONFIRMED_SAME_ATTEMPT=2`. This supports the narrow mechanism boundary in this toy only; it does not establish power-loss durability, arbitrary external-effect correctness, or distributed storage guarantees.

## Scope and next evidence

This host-side pilot is not the requested container-backed confirmatory experiment. The proper next step is a **distinct** preregistered Docker allocation, not a rerun of these seven cases. A useful next discriminator is duplicate/out-of-order delivery at the external-effect sink after the receipt has already been consumed, with independently audited effect cardinality and semantic state.

The earlier #5508 T0–T11 issue comments remain unchanged. This pilot adds a new process-kill boundary and should be read as exploratory evidence with a capture/provenance weakness, not a replacement for them.
