# A14 live recovery follow-up

**Disposition: HOLD.** The preregistered current-main V39 episode completed all 12 decisions and exited cleanly. It recorded 2 kills, 0 deaths, and no MAP01 exit. Health ranged from 61 to 100; no hard-health guard occurred, so the two-decision recovery question was not exercised. One useful scorer event occurred in the episode, but none landed within a controller model interval.

The independent cancellation audit passed: all 13 matched cancellations were accounted for, including 7 verified-empty terminal receipts with no active input lease and 6 token-matched active-lease releases. All 46 per-key release transitions matched owner key-up receipts, and all 23 terminals were verified empty. These are X11 owner/server receipts, not hardware key-state or game-consumption proof.

The initial frozen audit's `FAIL` is preserved unchanged. Its specific blanket cancel-to-`input_released` predicate failed for no-lease cancellations. The independent custody auditor and reconciliation v3 instead verify those cancellations through their empty terminal receipts, classify all 13/13 as accounted, and leave the episode's overall disposition `HOLD` because the hard-health and useful-feedback-during-inference gates were not exposed.

The app-server stderr contains a models-cache warning and a process-group termination warning; both processes nevertheless exited 0 and all 12 turns completed. The episode is one descriptive observation, not a causal comparison or task-completion result. Raw protocol and image artifacts remain in the private local allocation output; this package contains aggregate results only.

The allocation used current main `a6343bb76e4dc0a4afa32a29c8a485a617faeff8`, seed `990624`, and `gpt-5.6-luna` at low effort. It did not retry A04, A13, or any earlier allocation.
