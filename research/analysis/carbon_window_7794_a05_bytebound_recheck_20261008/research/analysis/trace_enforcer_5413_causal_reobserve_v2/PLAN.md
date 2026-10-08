# Issue #5413 successor T1 — reordered stale responses

Frozen source main: `bc57d55d4e0a4e75d1945d541ed27fce7cb2b955`.

## H / T / D / C / U

- **H:** After a second invalidation supersedes a pending reobserve request, delayed responses from the older generation cannot clear the new invalidation or admit an action. Only the current request/current generation/strictly newer observation sequence can restore admission; polling remains idempotent.
- **T:** Exhaustively enumerate every trace of length 0–6 over the seven frozen T0 events (137,257 traces). Stream each candidate transcript to gzip JSONL so the finite run does not retain the entire result matrix in memory. Run one fixed test suite, one runner, and one separately implemented streaming raw-only auditor with five corruption controls.
- **D:** Pass this extended boundary rung only if the independent reference matches all 137,257 transcripts; stale actions remain blocked; old/unlinked/replayed responses do not discharge current invalidations; one request is emitted per pending generation despite repeated polls; a linked fresh response permits an action; and all five corruptions are rejected. Any mismatch is STOP/FAIL; no retry.
- **C:** CPython 3.11.9, Windows host CPU, standard library only. Synthetic event IDs/generations/sequences are trusted labels; no live capture, clock, X11, MAP01, model, or task effect.
- **U:** This is bounded bookkeeping evidence only. It does not authenticate a capture source, establish response deadlines or useful feedback, prove runtime safety, or close #5413/#59. No GPU training is relevant to this finite discrete event enumeration. Docker is not invoked because #5085 has no allocation for this work and container isolation is unnecessary for the standard-library state machine.

## Fixed domain

The alphabet remains exactly `INVALIDATE`, `POLL`, `OBS_MATCH`, `OBS_UNLINKED`, `OBS_REPLAY`, `OBS_OLD_REQUEST`, `ACT`; maximum trace length is six. T1 is distinct from the already merged T0 depth-four allocation: it specifically covers delivery after request supersession, including the length-six invalidation/request/invalidation/request/old-response/action sequence. Source hashes and expected cardinality are frozen before test/runner/auditor execution.
