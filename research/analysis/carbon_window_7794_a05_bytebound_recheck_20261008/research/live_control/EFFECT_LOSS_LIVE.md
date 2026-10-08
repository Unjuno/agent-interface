# Tracking loss after displacement: live decision to avoid another move

The inverse of the false visual goal now reproduces through the actual caller.
In `effect-live-03`, the controller makes one correction, then loses the target
under an injected occluder. It returns `needs_decision`, zero completed steps and
a verified release. After GUI save, the independent checkpoint reports the target
at x=66.94915, with y/width/height=50/40/30: the declared geometry task already passes.
The assistant reads that result and finishes without another displacement.

## Fixed perturbation and actual use

The new explicit backend candidate is copied from the prior appearance fixture.
`effect_fault_backend_v2.py` counts servo snapshots and maps one white private X11
child rectangle at `[560,337,140,108]` immediately before snapshot 2. This is a
fixed event-count trigger, not a condition on the saved score, model decision, or
hidden application state. It obscures the source/search region after the first
correction in this run. Injection records remain separate from controller events.
The overlay is removed before the subsequent save program, as in the prior fixture.

The current shared servo policy, owner/lease guards, checkpoint scorer and caller
steps are unchanged. New explicit entry/socket/runner versions pin this fixture
before a fresh seed-220 session. The precision target is the runner's 20 screen px
at 118% zoom, not the old ready-event randomized `goal.dx`.

The assistant views the initial image and submits the declared servo. The first
feedback reports displacement zero and corrects the physical pointer to (648,391).
The next captured target region is white; tracking returns `lost` and `finish`.
The successful-servo card correctly falls back to the full detailed receipt.
Its terminal and feedback records, input-state details, and selected image are
reviewed. The toolbar still shows x=66.949, although the target is obscured.

Next the assistant explicitly submits the ordinary Ctrl+S/settle program. The
unobscured saved image shows the shifted selected rectangle. After reviewing the
image and save-state fields, the assistant requests `effect`; it returns success
before finish. `model-decision.json` records the choice to finish without additional
displacement, referencing the reviewed report, checkpoint reply and saved image
hashes. The final independent evaluation passes and the bridge exits with code 0.

This is one model decision informed by an independent benchmark oracle, **not** a
general autonomous recovery policy. No claim is made that the model selected the
same action without seeing the oracle. The fixture directly removes its own
occluder; the model did not discover or implement general occlusion removal.

## Evidence

`audit_effect_loss_v1.py` checks source pins, all seven socket exchanges against all
40 runtime events, command identity, detailed receipt reconstruction, eight exact
PNG/AIT frame pairs, checkpoint artifact/score and save-terminal attribution, final
saved geometry, and release records against owner evidence. It verifies the single
correction precedes injection, the controller then reports loss, and **zero pointer
admissions occur after that loss**. Only `servo` and `save` programs are submitted.

Initial capture to effect sampling was 47.300572985 s; servo terminal to effect was
25.409390533 s. These intervals include assistant review and tool gaps. There is
no matched speed comparison or actual model token/cost accounting. Process exit is
observed, but independent per-child cleanup inventory is still absent. Geometry
scoring does not establish full SVG equivalence or general visual target identity.

Reproduction of the audit requires an unused copy of the output location because
`results/effect-live-03/audit.json` is written exclusively:

```sh
python3 research/live_control/audit_effect_loss_v1.py
```

## Next decision boundary

Both opposite contradictions are now covered by live caller evidence: apparent
visual success with failed effect, and tracking loss with already achieved effect.
Do not add more near-identical injected cases merely to accumulate passes. The next
useful step is to decide task effect from ordinary GUI-visible evidence (for this
app, selected geometry fields), record the decision **before** requesting the
independent score, and then score it. This separates user-available evidence from
benchmark oracle assistance. It should preserve the controller failure and measure
the full observation/decision/recovery cost; current 25 s diagnosis is not human-like
tempo. Runtime/controller defaults and Research Freeze status remain unchanged.
