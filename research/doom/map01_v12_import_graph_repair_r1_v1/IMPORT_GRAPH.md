# Import graph audit

- Base: `main@5432f3aa2374753e7ab206ad5e1f3f093ac0a641`
- `research/doom/session_v7.py` blob SHA: `b8f044cd52449f2a72538232bb162a7a01155d2b`
- `research/live_control/session_v8.py` blob SHA: `4f33111fa27474d6eb4d3f8db22fae4bae7626c8`
- Entry import: `doom.session_v7 -> live_control.session_v8`
- Nested import in v8: `live_control.session_v8 -> session_v7` (bare module name)
- Conflict: the bare name can resolve to the shared-runtime v7 module rather than the
  `research/doom/session_v7.py` entrypoint, depending on `sys.path`; the current
  entrypoint also prepends `research/live_control`, making this boundary
  implicit.

## Required repair invariant

The repair must make the dependency explicit and acyclic, preserve the public
`Backend`/`suite` symbols, and leave all retained source and fixture bytes
unchanged. A passing import smoke is infrastructure evidence only.
