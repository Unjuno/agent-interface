# Separate versus combined feedback: paired pilot and image discrepancy

The preregistered `results/feedback-pilot-01/plan.json` specifies two seeds and
AB/BA order: A separate image retrieval, B image in the action call. Both use the
same frozen v7/client, full output, one-second write_stdin yield, 2200-token text
limit and observation-anchored25s deadlines. Initial images arrive with startup
in both arms. Same active assistant thread is used throughout; independent model
identity/settings and actual token telemetry are unavailable. This is not a
qualifying same-model efficacy study.

| Order | Seed | Method | Outcome | First acceptance -> finish command |
|---|---:|---|---|---:|
| A1 | 990801 | Separate | Completed, alive | 59.001s |
| B1 | 990801 | Combined | Completed, alive | 23.013s |
| B2 | 990802 | Combined | Completed, alive | 29.461s |
| A2 | 990802 | Separate | Aborted, unfinished | 75.388s to abort, not completion |

Initial world pixels are identical within each pair. A1/B1 each issued Left140ms
then Space350ms. B2 issued Left200ms then Space350ms. A2 issued Left200ms, but
its planned Space350ms arrived after the25s validity window and was rejected
before input. It then requested a clock and a new read-only observation. The
assistant perceived that recovery image as nearly black and aborted. This failed
case and recovery time remain included; do not calculate an aggregate completion
speedup using its abort time or exclude it as an outlier.

All28 frames reconstruct exactly; raw/delivered/client records match, terminal
releases and owner closes verify. There are eight accepted programs total, but
A2's second program is recovery observation, not firing. A2 has one rejected
shot and one clock request; the other cases have neither. Acceptance gaps are
20.140s,15.126s,15.809s,54.980s respectively, with the last ending at recovery.

## Important correction: black presentation is not a black saved PNG

The final A2 world crop has99.742% nonblack pixels. Reading the exact saved
005.png with view_image detail=original after shutdown showed a normal scene.
The older failed `shared-assistant-01/002.png` also contains a normal scene
(99.767% nonblack world pixels); its current bytes exactly match the previously
published Git blob. Re-reading it at original detail also showed the full scene.
See image-discrepancy.json for hashes and scope.

Thus earlier descriptions of a black *saved image* or confirmed game-rendering
failure were too strong. What was established was the assistant's perceived
black presentation during control. The original encoded tool-return images were
not archived, so the exact source—image preparation, delivery/presentation or
interpretation—is unresolved. Requesting original detail succeeded on these
rereads but is not yet a proven fix. Preserve failed task outcomes; they do not
become successes just because the retained images later prove usable.

## Interpretation and next action

Combined delivery completed both pilot cases and avoided an image-only model
boundary per successful program. The result supports further investigation, not
a population success rate or general speedup. Only two seeds, carryover learning,
variable orchestration delay and the presentation discrepancy remain. A1's long
finish delay is retained, not silently replaced with its earlier runtime terminal.
Its startup also included an extra source read in the launch tool output; that
does not alter runtime state but is additional context, further limiting inference.
Recorded tool body spans use a separate wall clock and do not measure model
receipt or semantic recognition time.

Before expanding timing trials, verify the complete observation delivery path:
saved PNG -> encoded tool image -> model-visible presentation, with explicit
detail and captured artifact hashes. Continue full event delivery; latest-feedback
files alone are not critical-event retention. No architecture/performance
promotion or Research Freeze nomination follows this pilot. The human-tempo
goal remains unachieved.

Re-run `python research/doom/audit_feedback_pilot.py` to verify sources, cohort
membership, images, delivery, expiry rejection and outcome/timing calculations.
