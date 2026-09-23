# Actual assistant guided-pointer pilot — 2026-09-13

This is an unsuccessful assistant-use trial of the published interactive_v12 /
session_v15 candidate, with full failure evidence retained. It changes the next
experiment: a short reply window that works with a local image controller does
not establish a workable remote assistant feedback loop.

The assistant viewed the initial 1280×800 Inkscape image, selected the rectangle
center at (619,390), issued an initial path to (631,390), viewed the feedback image,
and requested correction to (654,390). Decisions used the displayed screenshots;
no local color detector chose these commands. This reused the known fixture and
previously studied movement pattern, so it is not a held-out perception test.

The feedback still showed the object at its original position. The correction
arrived **13,390.9 ms after pointer_yield**, **8,474.2 ms after the reply deadline**.
The 5,000 ms reply timeout was already the candidate's maximum. Input independently
released; the terminal was `needs_decision`; the obsolete reply was rejected.
Saving and independent evaluation then confirmed x=50, y=50, width=40, height=30:
the object had not moved and task success was false. This is measured end-to-end
assistant/tool response latency, not an isolated model inference measurement.

Two additional ergonomics failures occurred before input: the published report
incorrectly showed point arrays instead of `{x,y}` objects, and the assistant
guessed `ctrl` while the backend requires `Control_L`. Both entire programs were
rejected. The report's point example is corrected. The current ready message lists
field names but not full nested types, enum values or constraints; a self-describing
validated operation schema remains needed, consistent with Issue #5.

`guided-self-use-01` was a launch-only attempt: a non-PTY shell gave stdin EOF,
so the entrypoint exited without executing a task. `guided-self-use-02` used a
persistent PTY and exited with code 0 after explicit finish and false task scoring.
Both launches are retained. `audit_guided_self_use.py` checks the recorded source
hashes, seven exact frame reconstructions (including reused PNGs), release,
late-reply rejection and failed scoring. It does not independently prove every
child process exited; the entrypoint's finally cleanup ran before normal exit.

## Next experiment

Keep the five-second result as a failed baseline. Do not infer that longer holds
or faster local input solve planner latency. Compare a planner-declared bounded
local visual-effect goal against repeated remote correction, with explicit target,
duration/update limits and anchor-loss handling. Issue #5's deterministic visual
anchor/servo proposal is now supported as an experiment priority, not as a proven
general feature. Predeclare fresh positions and distractors, independent endpoint
and collateral scoring, and record planner boundaries. Any longer-window remote
comparison must be a separate declared condition with unchanged original authority.

The previous scripted ±1 px results remain valid within their narrower scope.
No runtime promotion, human-speed result, token saving or freeze qualification
follows from this assistant trial.
