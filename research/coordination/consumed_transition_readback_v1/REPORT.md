# Consumed Transition Readback Result

Decision: `PASS_CONTENT_BOUND_CONSUMED_TRANSITION_READBACK_SCOPED`

## Question

After a one-use confirmation transition has actually committed but its success response is not supplied to recovery logic, can exact content-bound readback prevent a fresh-confirmation replay of the same logical transition?

## First outcomes

| Case | Recovery evidence | Recovery action | Final generation |
|---|---|---|---:|
| naive reissue | success response unavailable to classifier; no content-bound recovery | install same-content rev2, replay logical transition | 3 |
| exact readback | one GET exactly equals frozen g2/rev1/consumed after-state | `ALREADY_COMMITTED_SELF`; zero refresh/replay writes | 2 |
| readback unavailable | `UNAVAILABLE` fixture | `UNKNOWN_COMMIT`; zero refresh/replay writes | 2 |

The negative control demonstrates a concrete duplication mode. The original g1->g2 consuming transition had already committed. Treating the unobserved response as evidence that it did not commit, minting rev2, and replaying the same increment advanced the state again to g3.

In the candidate arm, one exact GET recovered the already-committed consumed state, so recovery stopped without minting a new confirmation or repeating the transition. When no readback evidence was available, recovery remained unknown and also stopped rather than guessing.

## Measured totals

- first consuming transition writes: 3
- successful measured writes overall: 5
- naive recovery refresh writes: 1
- naive recovery replay writes: 1
- candidate recovery refresh writes: 0
- candidate recovery replay writes: 0
- classifier real GETs: 1
- classifier unavailable observations: 1
- evaluator-only GETs: 1
- fresh-SHA retries: 0
- naive duplicate advances: 1
- candidate duplicate advances: 0

## Interpretation

One-use confirmation consumption prevents direct reuse of the same confirmation, but it does not by itself tell a caller whether a prior consuming transition committed when the success response is unavailable. Reissuing fresh confirmation authority under that uncertainty can duplicate the same logical increment.

An exact, content-bound readback of the expected consumed after-state is sufficient in this scoped fixture to classify the transition as already committed and stop recovery. Lack of readback evidence remains `UNKNOWN_COMMIT`; elapsed time or response absence does not authorize refresh/replay.

## Boundary

This is sequential GitHub-backed fixture evidence. It does not establish network failure semantics, authenticated transition-intent identity, simultaneous-request linearizability, distributed consensus, crash/power-loss behavior, confirmation production authority, external-effect safety, or production exactly-once execution.

The negative control intentionally lacks a durable transition-intent identity. A stronger successor is to bind a stable logical transition id into the canonical record so exact replay can be recognized semantically even when representation or surrounding canonical metadata changes.

`verify.py` is retained deterministic checking code. No independent execution of that verifier is claimed here.
