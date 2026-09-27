# Actuation lineage identity validation v1 — first outcome

Disposition: `PASS_ACTUATION_ID_VALIDATION_SCOPED`.

The exact merged parent accepts malformed actuation identities as lineage keys. In fixed controls, `Actuation.actuation_id=None`, `''`, and `0` paired with matching independently scored useful effects each produced `useful_bound=1`.

The candidate changes only lineage-ID admission before delegating to the unchanged parent `analyze()`:
- actuation ID: non-empty `str` only;
- effect actuation ID: `None` (explicit unbound) or non-empty `str`.

Frozen formal, one invocation / zero reruns:
- valid-domain differential: 50,000 / 50,000 exact parent-candidate equality;
- malformed-domain: 50,000 / 50,000 rejected, split 25,000 malformed Actuation IDs and 25,000 malformed non-None EffectEvent IDs;
- explicit `EffectEvent.actuation_id=None` remains `useful_unbound=1`, `useful_bound=0`;
- Unicode non-empty valid IDs preserve semantics;
- existing duplicate-valid-ID rejection is unchanged;
- model/network/task-input/authority actions: 0.

Measured formal loop wall reported by `/usr/bin/time`: 3.19 s, max RSS 92,720 KB, in the current container. This is diagnostic only, not a performance claim.

Independent audit passed with no errors. Four copied-result corruption controls (valid count, malformed count, source hash, disposition) were all rejected by the auditor. No formal rerun was executed.

Scope: synthetic same-process standard-library evidence. This does not test temporal causality (#950), live X11 release/effect timing (#869), MAP01, global uniqueness, or a production runtime boundary.
