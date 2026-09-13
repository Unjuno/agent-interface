# Registered pair 2 — helper arm completed, reference arm pending

Pair 2 follows the registered Inkscape seed-202 B-then-A order. Only B has run so
far. The measured `recovery_pair2_v1.py` runner is frozen for the subsequent A arm;
pair 1's measured runner and result were not altered.

The protocol's depth-3 prose specifies **three additional historical clock
boundaries before the own clock**. The runner records that literally: after an
observe-only advance, it issues and receives three explicit setup clocks, then
deliberately invokes the stale initial batch. That stale attempt returns the
earliest clock boundary and stops without submitting its Right hold. Recovery
therefore requires four additional reads: three historical boundaries plus the
own clock. The pre-query execution metadata states both numbers. This is not a
claim that depth 3 means three total reads; retain actual counts in comparison.

B's frozen reader traversed these four received slices in one orchestration call.
The assistant received the complete assembled history and original image together,
reviewed it, then explicitly submitted the registered move/save steps. The program
completed without interruption. The independent legacy score and saved SVG agree
on x=52, y=50, width=40, height=30, transform absent. This is a rightward-motion
contract, not a requested-distance precision result.

## Verified B evidence

- Four read-only recovery exchanges, with no command field in any read request.
- Each of the first three recovery boundaries equals its recorded setup clock;
  the fourth contains the original stale attempt's own request identity.
- The assembled actual history is exactly the later move caller's source batch.
- Fourteen total socket exchanges cover all 47 unique raw events, including overlap.
- Nine exact AIT/PNG frames, pinned sources, completed terminals and input release,
  and independently saved SVG fields pass the audit.
- Capture-to-evaluation duration: **59.039201361 seconds**.

Bridge exit zero and the combined history/image experience are recorded in the
conversation-derived presentation metadata. As before, this old entry provides
no structured per-child cleanup artifact. Exact model identity/configuration,
model receipt times and actual token/cost accounting remain unavailable, so model
performance qualification is not met. No causal or paired speed/call-count effect
is reported before A runs. Grouping four network reads into one model call does
not eliminate those network reads.

## Continue without rerunning B

Study progress is **3 of 8 episodes**, with five remaining. Next execute pair 2 A
with this same runner, seed 202 and preparation. Its `recover1`, `recover2`,
`recover3`, `recover4` stages must be separate model orchestration calls, one read
each; inspect the returned history each time and do not batch those stages into a
single tool invocation. Move only after reviewing the own-clock history/image.
Keep every failure or recovery in A. Do not substitute a scripted loop for these
model boundaries, and do not rerun B to align with later observations.

```sh
python3 research/live_control/audit_recovery_pair2_b_v1.py
```
