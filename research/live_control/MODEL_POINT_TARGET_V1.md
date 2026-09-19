# Model-point-derived target region v1

Status: hold as an opt-in research candidate. The preregistered Chromium gate and
the Windows/WSL artifact audit pass, but post-hoc contract review finds that the
prompt requests absolute screenshot coordinates while the caller assigns the
`window_content` transformation frame. General target identity, automatic region
and frame authorship, cross-application transfer, cost reduction and human-tempo
control remain unproven.

## Question

Can the runtime turn a model-authored point into a short-lived target handle
without requiring the caller to transcribe an absolute target box, while refusing
to mint the handle if that part of the screen changes during model inference?

The preceding handle studies used a caller-authored rectangle. That rectangle was
then privately bound to the observation, focus, surface and geometry, but the
interface had not established that the target geometry came from the model's own
grounding.

## Candidate

`target_handle_mint_from_point` accepts:

- the exact retained source-observation sequence;
- one model-authored point and an explicit coordinate frame;
- a bounded even region size;
- lifetime, freshness, search and transformation limits; and
- a unique session alias.

For v1, the runtime derives a centered rectangle from the point, captures a fresh
observation, maps the rectangle through the current surface binding and compares
the exact RGB patch. It mints a private-ID-backed alias only when the source and
fresh patches are byte-identical. A mismatch emits
`target_handle_mint_from_point_refused`, creates no handle and ends the program as
`needs_decision`. Normal target input still performs admission-time revalidation.

The session retains at most 16 exact observation/image pairs. This is bounded
episode memory rather than a general visual object tracker.

## Preregistered live pair

`chromium-model-point-target-pair-01` freezes two same-seed Chromium sessions in
changed-target then stable order. Both use the identical coordinate prompt,
current 1280x800 screenshot, controlled empty workspace and Luna-low. The fixed
region size is 24x14. There is no retry or parameter repair.

Both coordinate calls return point `[270,243]` inside Save with strict action
shape. They report 9,285 and 9,284 input tokens. Cost and observed provider model
identity are unavailable.

The prompt asks the model for absolute screenshot x/y. The caller separately
labels that point `window_content`, which means the runtime translates the region
by the change in bound-window origin. This is sufficient for the constructed
surface move, but the model did not author or explicitly confirm that frame. The
numeric basis and transformation membership therefore remain separate, with the
latter still supplied by task code.

In the stable arm, source sequence 12 and fresh sequence 13 produce the same exact
patch digest. The runtime derives box `[258,236,24,14]` and offset `[12,7]`, then
mints alias `save_form` without exposing the private registry ID. After the X11
surface moves by `[20,8]`, combined fresh observation/revalidation resolves point
`[290,251]`. A second no-image Luna-low call reports 8,012 input tokens and emits
the exact handle relation. Admission revalidates again, admits only move and
button-down, saves `t991014`, verifies release and passes the independent file
oracle. The case uses 16 durable calls.

In the changed-target arm, the same surface navigates to `about:blank` after the
coordinate model returns. Minting captures current sequence 19 and compares the
predicted region with retained source sequence 12. The digests differ, so the
runtime creates no handle, admits zero target pointer operations, verifies release
and creates no submission. The independent result is false by construction. The
case uses 10 durable calls.

The independent audit verifies preregistration hashes, model runner configuration,
prompt identity, input-token records, patch digests from decoded images, private-ID
non-disclosure, binding translation, pointer admissions and independent output.
All 35 exact frames reconstruct from `.ait` on Windows and WSL.

## Decision and limits

Retain the operation code and frozen evidence because it removes the
caller-authored absolute target box in this experiment and closes one
stale-grounding race before handle creation. Hold promotion because v1 still
depends on caller-chosen `window_content` membership and a24x14 region size, one
known button, exact pixels and a constructed page-change negative. Exact matching
may refuse animated, highlighted, scaled or restyled targets, while repetitive
patches require separate ambiguity controls.

This pair has two image-coordinate calls and one no-image handle call. It is not a
matched speed, token or cost comparison. It provides no unknown-application,
cross-domain, causal latency or human-speed claim.

The next gate must first align coordinate semantics: either ask the model for an
explicit transformation frame in addition to screenshot coordinates, or define a
runtime rule that derives content membership independently. It should then use a
preregistered different-domain task where the model point derives the target
region without a caller-authored box, with a visually similar or transient
negative, independent semantic scoring and actual model-boundary timing/tokens.
Region-size authorship should remain explicit until a separately tested bounded
proposal rule exists.

## Reproduction

The fresh GUI/model allocation is preserved and must not be rerun in place.

```text
python research/live_control/probe_model_point_target_v1.py
python research/live_control/audit_chromium_model_point_target_pair_v1.py
wsl -e bash -lc "cd '/mnt/c/Users/junny/Documents/New project/agent-interface' && python3 research/live_control/audit_chromium_model_point_target_pair_v1.py"
```

Artifacts: `research/live_control/results/chromium-model-point-target-pair-01/`.
