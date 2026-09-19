# GUI geometry readback and repair before independent scoring

In `gui-effect-live-01`, the assistant diagnoses an unmet displacement from the
ordinary Inkscape toolbar, repairs the selected rectangle through that toolbar,
and commits a predicted-success decision before requesting independent evaluation.
The eventual saved SVG passes at x=66.949997, y=50, width=40, height=30.

This removes the checkpoint oracle from the **decision path in this episode**.
It does not repair visual target identity or demonstrate an unfamiliar-task policy.
The replacement fixture and layout are familiar from prior research; this is not a
blinded or held-out trial. The experimenter knows the fixture and target.

## Recorded interaction

The new `gui_effect_live_v1.py` runner pins the existing replacement backend and
socket v2 with seed221. Runtime/controller/defaults are unchanged. Its declared
precision task remains 20 screen px at 118% zoom, x66.95±1 and y/size50/40/30±0.1,
independent of the old ready-event randomized goal field.

1. Initial image is viewed. The ordinary servo returns completed/local-goal despite
   the underlying false visual effect. Its card still says task success unknown.
2. After explicit GUI save, the unobscured screenshot shows toolbar X=50.000,
   Y=50.000, W=40.000, H=30.000. No effect/evaluation command has been requested.
3. The assistant writes a GUI-only decision: unmet; set selected X to66.95. Its
   exact file hash is included in an ordinary clock command and echoed by the
   runtime before recovery starts. This is a historical marker, not input authority.
4. A new normally admitted program clicks X at(560,106), uses Ctrl+A, types66.95,
   presses Return and settles. No XML editing, hidden object mutation or engine
   action API performs this repair.
5. The assistant views the repaired image, then explicitly saves again. The saved
   screenshot reads66.950/50.000/40.000/30.000. A second GUI-only decision predicts
   task success; its hash is echoed before any independent score is requested.
6. The saved-effect checkpoint and final evaluation both pass. The bridge exits0.

The runner stores both source decisions and copies; commits bind the image hash and
previous report hash. The recovery's initial history is the local concatenation of
two contiguous, previously received event slices (save reply and decision clock).
It is labeled received history, not a fabricated socket response. A new ordinary
clock/admission still checks the current image sequence and bounded deadline.

The environment fixture itself removes its overlays before the save program. This
is not model-discovered occlusion removal. The assistant's GUI diagnosis and repair
follow that declared fixture transition. No intermediate independent score was
taken for the initial x50 state; the claim there is a recorded visual readback.

## Verification and cost

`audit_gui_effect_v1.py` checks the pinned sources; all13 exchanges against91 runtime
events; command identities; receipt reconstructions;19 exact PNG/AIT frames; owner
release records; contiguous recovery history; both decision file/image/report hashes
and echo ordering; and the final SVG hash, geometry score and evaluation.
Only servo/save/recover/resave programs are submitted. Both decisions precede the
first saved-effect event; the first also precedes recovery. The final visual values
agree with saved geometry within0.001. This proves internal record ordering, not
external authenticity, all possible side-channel exclusion or blindness to prior
knowledge. During this episode the assistant did not inspect the saved SVG before
requesting evaluation.

Initial capture to the runtime echo of the GUI-success decision took83.236127991 s;
to saved-effect sampling92.325825318 s. These include model/tool/review gaps, not just
execution. The extra two clock exchanges are commitment instrumentation. Thirteen
communications and19 observations are too much to claim human-like tempo. There
is no paired latency comparison, measured model input tokens or cost. Process exit
is observed; independent per-child cleanup inventory remains absent.

Audit output is exclusive at `results/gui-effect-live-01/audit.json`:

```sh
python3 research/live_control/audit_gui_effect_v1.py
```

## Next useful improvement

The evidence supports GUI-visible effect checks for this selected geometry task,
with independent scoring kept after the decision. More identical fault injections
would add little. Investigate existing observation/presentation machinery for a
bounded field-edit workflow: retain useful feedback and interruption evidence while
avoiding repeated routine image/state review at every typing substep. Compare
correctness and end-to-end recovery cost under changed target values or layout;
do not tune only this screenshot. Keep original failures, full records and candidate
defaults frozen. No general recovery, speed, token-saving or Research Freeze claim.
