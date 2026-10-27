# Independent review: #8119 projector repair

**Result:** no material defect found in the scoped production/test change. This is a technical review, not a merge or quorum vote.

The repair addresses the duplicate-release hole by removing each matched identity from the admission map and requiring the map to be empty at the end. A release can no longer satisfy another release slot for the same key while leaving a second admission unmatched. The unit test has a direct duplicate-release control, and the producer-composition test repeats the case with emitted fake-X owner/backend rows.

Identity fields are constrained to nonempty strings and a nonnegative exact integer step before they are used as dictionary keys. Attempt ordinals, batch positions, sizes, counts, and timestamps use exact integer checks, so booleans do not pass as integers. The projector also checks input acknowledgement and deadline chronology, deadline equality across admission/release/receipt, V3 release-batch schema and ordering flags, owner/token consistency, complete key-up receipt history, retry continuity, final UP state, and post-batch sample order. It accepts the real producer shape with the optional `operation=down` and `owner_sample_after_batch_available` fields absent, while rejecting either field when explicitly contradictory.

The retained red run reports 16 methods with 25 failures and 20 errors before repair. The retained green run reports all 16 methods passing after repair. Source snapshots in each run matched their SHA entries when read. The fake-X composition exercises the actual V12 owner, V3/V4 wrappers, and batch backend raw dispatch and publisher. Its tests directly call `raw`; they do not run backend `execute`, the Executor, Session, V39 controller loop, program parser/lowering, V15 main, or a game.

The accepted contract is intentionally narrow: down and up must share the same program step and deadline, and cross-step holds remain unready until stronger custody is available. The test for boolean attempt ordinals covers the same ordinary regression property carried by #8132; it is not a new formal finding. No live input, physical-keyboard, application-consumption, latency, or game-effect claim follows from these tests.

Source hashes and retained result identities are recorded in [review.json](review.json).
