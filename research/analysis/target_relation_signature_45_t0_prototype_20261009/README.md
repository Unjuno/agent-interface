# #45 relation-signature prototype (construction only)

This standalone prototype explores #45's same-session target-handle relation-signature idea. It is deliberately outside the runtime dispatch path. It accepts a source signature and a complete, fresh observation's candidate signatures; it returns only an advisory classification and never grants action authority.

The reference rule requires exact same-surface, same-container, same-role, same-label and same-relation evidence. Exactly one match returns `REVALIDATED`; duplicate exact matches return `AMBIGUOUS`; a compatible candidate whose relations changed returns `UNKNOWN`; a different surface/container/role/label returns `NO_MATCH`. Incomplete observation data returns `UNKNOWN`, and generation disagreement returns `STALE`.

This distinguishes three narrow controls: translation/reorder with preserved relation signature; an identical label in another pane; and an exact same-signature duplicate. A reflow that changes the relation signature is conservatively `UNKNOWN`. The prototype does not establish that relation witnesses are observable or trustworthy in a real UI, nor that these fields preserve semantic identity. It does not use app-internal IDs or scorer-only state in the implementation, but the unit fixtures are authored and do not validate any production observation adapter.

## Validation

Construction tests were run from this directory on CPython 3.12.13 / macOS 27.0.1 arm64:

```sh
python -m unittest discover -s . -v
python -O -m unittest discover -s . -v
python -m py_compile relation_signature.py
```

Both test runs passed 7/7. This is prototype unit-test evidence, not the separately proposed #45 T0. That isolated experiment was not started because the current OrbStack daemon could not return the shared container/image inventory: `docker ps` and `docker images` failed with containerd blob read errors. No container was created or modified. No live GUI, model, user data, or input was used.

## Limits and next test boundary

The tests only validate deterministic classification logic over caller-supplied records. They do not validate capture completeness, freshness beyond a monotonically increasing generation field, identity-witness provenance, confidence thresholds, false-bind rates, task effects, or re-grounding cost. These remain gates for a separately frozen and isolated T0 corpus and independent raw-only audit. The module must not be wired into action admission based on this prototype.
