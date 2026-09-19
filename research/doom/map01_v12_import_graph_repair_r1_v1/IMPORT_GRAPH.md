# Import graph audit

- Historical base used by this audit: `main@5432f3aa2374753e7ab206ad5e1f3f093ac0a641`
- `research/doom/session_v7.py` blob SHA: `b8f044cd52449f2a72538232bb162a7a01155d2b`
- `research/live_control/session_v8.py` blob SHA: `4f33111fa27474d6eb4d3f8db22fae4bae7626c8`
- Intended fresh entry path: Doom script inserts `research/live_control` at `sys.path[0]`, then imports bare `session_v8`.
- Intended nested path: `live_control/session_v8.py` imports bare `session_v7`, which resolves to `live_control/session_v7.py`; this is the intended, acyclic shared-runtime chain.
- Actual failure boundary: when `research/doom/session_v7.py` is itself loaded under the top-level module name `session_v7`, its partially initialized module occupies `sys.modules['session_v7']`. The later bare import from `session_v8` then re-enters that Doom module and forms the observed cycle.

The repair target is therefore the Doom entrypoint's top-level module identity /
loading boundary, not the normal `live_control/session_v8 -> live_control/session_v7`
resolution. The import-only gate must test both the intended live-control
resolution and the failure-triggering entrypoint load separately.

## Required repair invariant

The repair must give the Doom entrypoint a non-colliding module identity or an
explicitly isolated loader, preserve the public `Backend`/`suite` symbols, and
leave all retained source and fixture bytes unchanged. A passing import smoke is
infrastructure evidence only.
