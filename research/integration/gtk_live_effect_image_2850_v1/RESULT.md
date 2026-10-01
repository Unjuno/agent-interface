# #2850 local live-application effect prelight

Date: 2026-09-20

Decision: `COMPLETED_UNSCORED_GTK_LIVE_EFFECT_PRELIGHT`

This is a bounded local Docker/Xvfb prelight for #2850. It is not formal
#2606 acceptance and does not replace the retained #2672 result.

## Provenance

- Base image: `agent-interface-gtk-fixture-v2:2748`
- Base image digest: `sha256:65c35be50f37bca68c35f514e62dc1a16daf75f5b6b663bab349ea928667a739`
- Additive package: `python3-xlib_0.33-2` (with `python3-six`)
- Local image tag: `agent-interface-gtk-live-effect-2850:v1`
- Runtime: `--network none`, read-only source mount, tmpfs `/tmp` and `/run`
- Runner: `research/integration/golden_v3_second_domain_2246_v1/gtk_adapter_runner.py`

## Observed result

The GTK fixture was the same application before and after the operation. The
runner typed `gtk2492`, dispatched Ctrl-S, and the application emitted:

```json
{"saved": true, "text": "gtk2492"}
```

The retained raw result reported `native_status=completed`, `program_completed`
true, 9 completed operations, a 400x180 observation frame, `authority_granted`
false, verified empty key/button release, and zero model/provider calls. The
independent effect receipt was `saved=true` for the declared application
operation. The X11 window identity was `2097155`.

The adapter-level result remained `partial` and `task_success=null`, while the
runner's separate effect field reported `task_success=true`; this boundary
disagreement is retained as an unresolved scorer/receipt issue, not promoted.
The stale-target refusal control also passed.

## Scope and next step

This proves that the dependency-repaired local image can reach a real GTK
application operation and observe its effect. It does not cover the full fixed
order, negative control, all safety cases, or formal receipt scorer required by
#2850. The next successor must preserve this image provenance and repair the
adapter/scorer boundary before formal promotion.
