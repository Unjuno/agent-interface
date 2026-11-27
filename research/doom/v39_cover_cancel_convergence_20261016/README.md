# V39 cover cancellation: historical custody and current boundary

This converges [PR #8384](https://github.com/Unjuno/agent-interface/pull/8384),
exact head `fd52341c4686893ff3de8795c9a5b671c7d20f9c`, onto main base
`ccc82e39fca9eb60413e93e9a0fbef051f48d4cd`. All 15 original files are retained
at their original paths with identical Git blobs. The eight original checksum
references match. A01/A02 remain pre-candidate infrastructure STOPs; A03 remains
historical in-process construction, not a current/live release result.

## Saved evidence audit

The original [A03 package](../v39_interrupt_cancel_composition_a03_20261008/README.md)
records 10 cases and an original auditor. The published review on #8384 correctly
identified that this auditor can replace held-button-release with a duplicate
cancelled-empty case and still print `6/6 invalid terminals refused`. The new
copied mutation reproduces this false PASS: only nine unique cases remain.
Neither original raw nor original auditor is changed.

The separate [saved-only auditor](../audit_v39_cancel_composition_saved_v2.py)
requires the exact ten frozen case IDs once each, frozen status/release conditions,
one exact ordered logical event inventory, and matching old/fresh answer summaries.
It reconstructs four accepted and six refused cases. Its tests reject 17 copied
corruptions. Initial review found Python equality accepted boolean-to-number
substitutions; three controls reproduced that failure before recursive exact-type
comparison repaired it. Both first results remain under this packet.

This verifies internal consistency of the retained authored evidence. It cannot
authenticate the producer, prove physical input state, or certify unrecorded
events. The recorded `cover_terminal` event was appended by the historical
producer after the helper returned; it is not a wire timestamp. Historical
planner-interrupt/cancel event ordering and the old partial release schema are
not current caller contracts. No historical producer was imported or rerun.

## Current caller check and remaining dependency

The existing two `test_cancel_invalidated_cover_order` methods fail on current
main because their old release fixtures omit `owner_release`, `keys_unknown` and
`key_state_errors`. Only those fixtures are updated; their existing ordering,
identity, write-failure and terminal assertions remain. The module is now in the
isolated affected-regression runner instead of silently being omitted.

A new finite characterization uses actual current V39 `cancel_invalidated_cover`
and `PersistentPlannerAdapter`, with an in-process planner transport and cancel
stream. While the test holds `interrupt_turn`, cancellation has been written and
flushed and the answer is locally invalidated, but an already supplied failed
terminal remains uninspected. After the test releases its own gate, the helper
reads and refuses that terminal. A JSON row records the held-transport boundary.
The keys-down fields are authored test data, not measured Fake X or physical keys.
There is no process IPC, provider, display, model, game, WSL or container run.

**Open implementation seam:** separate local answer invalidation/urgent input
cancel from waiting on remote planner acknowledgement, and retain the original
release obligation while terminal inspection proceeds. A bounded caller response
must not imply physical release, authorize a second writer, reuse a stale answer,
or automatically clear Executor's unverified-release fence. This change only
characterizes that dependency; it does not repair or bound it.

## Verification and custody

Final tested code `fe7381ed7a37a2b5e9c44154480890338c2cf638`: 40 isolated
modules / 289 methods, zero failures, one deliberate real-Codex handshake skip
(288 executed), in normal and optimized Python. Host: Windows, Python 3.13.14,
python-xlib 0.33, Pillow 12.2.0, MCP 1.30.0 and openpyxl 3.1.5. Final commands:
`../check_map01_control_regressions.py --output-dir <fresh path>`, adding
`--optimized` for the second mode. Logs and source/status summaries are retained
under `normal/` and `optimized/`. Normal started with a clean tree; optimized
records only the integration/consolidation documentation edits and this new
untracked explanatory packet. Tested code and definitions are unchanged.
Read-only review checks the five focused methods
in both modes, then verifies the corrected saved auditor and all 17 controls.

First current-main fixture failure, first repaired fixture run, old-auditor false
PASS, initial new-auditor checks and three type-counterexample failures remain.
Earlier full normal/optimized runs are intermediate: review controls were added
around that interval, so only the final runs qualify the final code version.
`preservation.json` records original blobs/checksums; `MANIFEST.json` hashes this
new packet. No formal consumed allocation was repeated. Optional remote CI is
not required or claimed as passed.

This supports closing #8384 as superseded after this preservation reaches main;
its author branch is retained. #59/#17 stay open for physical release, real
transport, replacement-session custody, independent effect, finite task recovery
and matched economics. No overall computer-control success is claimed.
