# V39 detectability-before-harm margin — read-only posthoc

## Question

Does one retained v39 model-wait cell identify a controller-visible threat cue
before the next typed HUD health decrement, and is the evidence
sufficient to claim an effective local intervention could precede harm?

This is a distinct read-only cell audit after #59 comment #5923276252's Astra
cell returned `HOLD_NO_MARGIN_ORACLE`. It uses v39 decision index 2 (the third
turn, model request at health 85) and does not repeat the Astra audit, rerun a
candidate, call a model/game, emit input, or use a container. This does not
revive or consume any #59 formal allocation.

## H / T / D / C / U

- **H:** In the selected v39 cell, retained frames show a threat no later than
  sequence 61, before the turn-2 model request. The request is followed by at
  least one typed HUD health decrement during model wait, so
  the source permits a positive cue-to-next-observed-loss interval. However,
  unless the same cell also identifies a guard decision, effective intervention
  and an irreversible-harm endpoint, the actual detectability-before-harm
  classification must remain UNKNOWN/HOLD.
- **T:** Bind current `main`, the v39 report, event stream, planner protocol,
  retained file manifest, v2 retained audit and six exact PNGs by SHA-256.
  Construction tests exercise endpoint selection, order, missing-endpoint
  refusal and mutation rejection. Then execute one independent read-only
  auditor over the immutable sources. Candidate/model/game/container/input
  invocations are all zero.
- **D:** `HOLD_NO_EFFECTIVE_INTERVENTION_BOUND_V39_CELL` if the prompt-bound
  health, exact typed timeline, visual witness, source hashes, and stale-action
  terminal reproduce, but the retained cell has no actual local guard gate,
  no effective switch/release attributable to such a gate, or no independent
  irreversible-harm timestamp. Any source, identity, ordering or receipt
  mismatch is `STOP_POSTHOC_AUDIT`; never infer success from health-loss timing
  alone.
- **C:** Health HUD loss is an observable damage proxy, not necessarily
  irreversible task harm; this one trace cannot bound future actuation delay.
  The visual note gives only “threat visible by sequence 61,” not earliest
  hazard onset. A previous v39 revocation's event-to-release sample is not a
  conservative delay bound for this cell and is not transferred as one.
- **U:** This cannot establish whether an already-authorized guard policy,
  preemptive cover, or faster model response would prevent damage. No causal,
  reliability, policy-correctness, or MAP01 success claim follows.

## Source and resource boundary

Publication base is current `main` `7f4121d3bab652b7c456db7469512bdefaa1a9ed`.
The source evidence is the already-published v39 first outcome. A07 on #5156
stopped before candidate because four nonterminal Created containers have
unresolved ownership (#5156 comment #5923277941); #5085 comment #5923297875
states the #59 request must not start while they remain unresolved. This pure
posthoc host audit does not access Docker/OrbStack and leaves all such resources
untouched.

## Visual read record

`VISUAL_READ.json` records the exact retained frames reviewed. The enemy sprite
is visibly present in sequence 61 and again in sequence 70; sequence 76/81/90
show subsequent typed HUD health 82/76/73. This is a manual posthoc visual
annotation, not an independent game-state hazard scorer and not a claim about
the earliest hazard onset. Exact PNG identities are frozen in `FREEZE.json`.
