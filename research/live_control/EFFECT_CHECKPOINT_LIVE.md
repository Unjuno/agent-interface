# Saved-effect checkpoint through the actual caller

The false visual goal now reproduces through the current bound clock/submit path
and successful-servo card. In both fresh trials the card returned `completed`,
local displacement `[20, 0]`, zero corrections, and **task success unknown**.
The saved rectangle remained at x=50. The card's `detail_review_required=false`
only concerns its selected program-consistency checks; it is not task success.

## Explicit candidate

`effect_checkpoint_v1.py` adds a fixture-only `effect` command to the experimental
interactive entry. It requires an idle executor and the latest completed program
to match the requested save ID and exact declared GUI Ctrl+S/settle steps. Under
the executor lock it copies the saved bytes to a SHA-256-addressed SVG, scores that
copy with the existing fixed-task scorer, and emits `saved_effect` with save ID,
save terminal time, artifact/hash, score and sample time. It does not close the
session, issue input, renew a lease, or feed the oracle to the local controller.

This is an independent benchmark evaluator. It is not a general desktop sensing
API and does not prove every unsaved GUI edit has reached disk. The declared task
is the runner's 20 screen px at 118% zoom, saved x=66.95±1 with y/size constraints;
the older ready event's randomized `goal.dx` is not this precision specification.

`effect_fault_backend_v1.py` injects private X11 child overlays before the first
servo feedback: white covers the original source and a red appearance is placed
20 px right. The original document is not changed by the injector. Overlay metadata
is saved separately as environment evidence, not supplied to the tracking policy.
Overlays are removed before the subsequent save program. This is a same-surface
appearance replacement, not native object replacement or arbitrary occlusion proof.

## Both attempts retained

| Trial | Outcome | Evidence |
|---|---|---|
| effect-live-01, seed 218 | `effect` rejected before forwarding | Old CommandOnce whitelist omitted the new operation; live process confirmed, then explicit finish returned failure |
| effect-live-02, seed 219 | `saved_effect` received before finish | x=50, expected 66.95; task failed despite completed local visual goal |

The first candidate is preserved. `effect_socket_v2.py` installs an explicit copy
of CommandOnce that adds only `effect` to the allowed operations. Default transport
and runtime entries remain unchanged. Request deduplication and payload-conflict
handling are retained. No uncertain write was retried. The second run is a new
candidate trial, not a replacement of the failed record.

The assistant viewed initial, servo-terminal and saved images in each episode,
read the compact servo card and detailed save/state fields, then requested effect
evaluation explicitly. In trial 02, the received saved-effect failure was read
before finish. No corrective displacement was submitted; this isolates diagnosis,
not completed recovery. Both bridge handles subsequently returned exit code 0.

## Verification and remaining work

`audit_effect_live_v1.py` verifies source pins, every successful response against
the exact runtime event slice, command request identity, compact receipt rebuilds,
14 exact PNG/AIT frame pairs, release evidence, unchanged saved x, and checkpoint
artifact/hash/score/save-terminal attribution. The first rejected request has no
runtime effect command. Trial 01 has 35 events/seven exchanges; trial 02 has 37
events/seven exchanges. The latter adds a real checkpoint response before finish.

Five offline checkpoint negative controls cover busy execution, wrong ID, failed
save, wrong steps and unknown fields. An existing successful SVG is a positive
scorer/checkpoint control; it is **not** a fresh live positive control. Duplicate
effect requests cause one write and changed-payload reuse is rejected.

Trial 02 initial capture to saved-effect sample was 39.777592869 seconds, including
assistant review and tool gaps. This is not model receipt time or a speed comparison.
Actual model identity, tokens and cost remain unmeasured. Source manifests are
listed components; no independent per-child cleanup inventory was added.

The inverse case—tracking loss after the task is already achieved—still needs a
fresh caller trial. Live recovery and appropriate production effect observations
also remain open. The visual identity failure is not fixed. No default promotion,
general compression/accuracy claim or Research Freeze follows from this experiment.

Audit reproduction (output is exclusive; choose a copy/worktree without the saved
audit output when rerunning):

```sh
python3 research/live_control/audit_effect_live_v1.py
```
