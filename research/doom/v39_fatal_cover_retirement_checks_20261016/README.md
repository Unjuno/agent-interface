# V39 fatal cover retirement without planner interrupt acknowledgement

Base `6d3fb8a2e8c3034060ebb60529fc7ffccaf251c0` repaired invalidated-cover
cancellation, but natural failed cover validation still requested synchronous
planner interruption before aborting a pending awaiter. The actual-main RED
test injects a finite 0.2-second interrupt wait: the original trace enters that
wait despite already having the failed terminal. This is an ordinary regression,
not a formal allocation or an estimate of real transport latency.

## Adopted behavior

`validate_planner_cover_terminal` preserves the existing strict status and
known-empty owner-release checks. On failure, `retire_failed_cover` locally
invalidates the matching planner answer and writes an exclusive
`fatal-cover-terminal.json` before trying to abort a pending planner transport.
No remote interrupt request is made. The original exception remains primary and
retains a copied receipt when invalidation, save or abort also fails. A preexisting
file is preserved. The saved receipt describes the future state at that instant;
it does not claim the later close succeeded.

All three existing main validation sites use this boundary: a natural terminal
received while waiting, a terminal drained when the answer completes, and the
post-answer cancellation terminal. Healthy renewal/admission rules and the
separate invalidated-cover cancellation helper remain intact. No new input,
retry, replacement authority or successful task effect is authorized.

## Evidence and verification

The actual-main harness substitutes transport/provider/game interactions. Four
new methods cover the ACK dependency and save-before-abort, pending/completed/
post-answer receipt preservation, an existing-file collision, and local
invalidation failure. Existing abort-fault and terminal/answer race controls stay
active; assertions now require zero remote interrupts for fatal validation rather
than the old one-request ordering. The first affected run's obsolete ordering
failures and subsequent repairs are retained rather than hidden.

The 21-method module passes normal and optimized Python and bounded read-only
review. Three selected tests additionally use the existing exclusive trace writer
to preserve `selected-traces/`: an interrupt that would block but is never called,
an actual Executor with an inert failing backend, and a local invalidation fault.
Each trace includes emitted events, commands, the original error/notes, future
completion and the receipt visible when abort begins. The real Executor case has
no native input; its neutral release is test data. Production failure cleanup is
replaced by a spy, so these are main-control-flow/retirement checks, not physical
release or production cleanup qualification.

Clean tested source `c7759b361fd0c53f28af2af55285b9571a8b1103`: 43 isolated
modules / 320 methods, zero failures and one deliberate real-Codex handshake skip
(319 executed), normal and optimized Python. Logs/source summaries are under
`normal/` and `optimized/`. The runner command is
`../check_map01_control_regressions.py --output-dir <fresh path>`, adding
`--optimized` for the second mode. Host: Windows, Python 3.13.14, python-xlib 0.33,
Pillow 12.2.0, MCP 1.30.0, openpyxl 3.1.5. The saved historical A03 fixture was
materialized from its current committed Git blob for this sparse checkout; no
historical producer was imported or rerun. `MANIFEST.json` hashes this packet.

## Remaining gates

The fatal path no longer depends on planner interrupt ACK. Planner close itself,
filesystem persistence, scheduler/GIL, native input send/sync/readback and physical
release are still not proven hard-time bounded. If close does not unblock an
awaiter, the enclosing executor join remains a recovery gate. A copied failure
receipt is retained evidence, not a physical-state certificate. Initial cover
failure before planner creation and other controller exits retain their existing
cleanup paths; this does not qualify every exit. Healthy interruption/absent-event
waits, replacement-session custody, independent task success, bounded recovery
and matched economics remain open in #17/#59/#57. No live display, model, game,
WSL/container or fresh allocation was launched; optional remote CI is not claimed.
