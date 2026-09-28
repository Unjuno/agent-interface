# Guarded tail expiry and explicit continuation

The existing guarded X11 bridge assigns a five-second deadline, but previously
checked it only around target captures. A fixed delay could finish after that
deadline and then start more text. The retained deterministic before control at
8346f25ba demonstrates a 25 ms wait followed by text with only 10 ms remaining:
the text mock was called after expiry. This is a source/control-flow reproduction,
not a physical input measurement.

The shared runtime now checks the unchanged deadline before each new key press
(including text characters and chord modifiers), while allowing key release.
The guarded wait sleeps until the earlier requested end or lease deadline,
rechecks after waking, and raises on expiry. The existing execution-failure path
preserves the prefix, marks the wait incomplete, releases input and stops the
remaining tail. Public guarded MCP still captures once after the result when
requested. No lease extension, automatic retry, new sensor or input owner is added.
Ordinary X11 dispatch retains its fixed-delay/admission-only behavior.

This applies the expiry/partial-effect principle recorded in the earlier
EXPIRY_OBSERVATION research to this synchronous production path. It does not
import that executor's separate owner, passive sampling or timing claims.

## Evidence

Runtime source: c1e910ab091f381c5a9f07287770b9a17b966050.
Portable artifact: 332b268d69f7a93902439d27923eded40a85e313a3f441ce3ba0b780780d52dd.
262 protocol and 118 harness checks passed. Seven new deterministic controls
cover interrupted/short/early-waking waits, expired presses with permitted key
release, expiry between chord keys, release failure, and unchanged inactive-guard
delay. Existing partial-execution and release quarantine checks remain passing.

Primary seed 991339 used that exact artifact through public MCP. Its preregistered
scope was one task: input t991339-1, wait 6000 ms, then suffix X. The original
five-second deadline interrupted the wait after 4844.855971 ms (prior captures
and typing also consumed the lease). The result remained execution_failed:
completed operations 0–5, failed operation 6, 25 emissions, no suffix step.
Release verification finished 0.966598 ms after the recorded deadline; the next
capture started 1.583769 ms after release verification. These are one trial's
runtime boundaries, not exact physical key-up, model-visible feedback, semantic
completion latency, a hard real-time bound or a latency distribution.

The primary viewed the exact entered prefix without X and verified empty held
input, then explicitly chose a separate Save. The independent submission journal
records the correct task-1 value exactly once. The six-task oracle remains false,
with tasks 2–6 unattempted. The expired call is never relabeled completed. Six
MCP calls include explicit close and read-after-close of the original failure and
image. Relay and fixture exited 0; GUI child cleanup codes remain 0/1/1.

The 113-file archive retains raw requests, reports, programs, images, review
receipts, oracle, build, before reproduction and check logs. Run:

`python3 -O runtime/results/guarded-tail-deadline-01/verify.py`

The read-only verifier checks file hashes, the exact interrupted program and
prefix, post-release capture order, unchanged historical result, reviewed
continuation, independent scoped save and reconstructed host timeline. It never
extracts or executes archived code.

## Remaining limits

Enforcement is cooperative: the host scheduler and blocking X11 operations can
delay detection and release. It does not continuously monitor focus, add a
held-input API, establish hard real-time safety, or change global pacing.
Typing that fits within the lease is still subject to application delivery and
must be visually checked. Actual model tokens/cost, matched task performance and
human tempo remain unmeasured. The newly added procedural world and #5156 caller
analysis remain research evidence with their original HOLD/scoped conclusions.
