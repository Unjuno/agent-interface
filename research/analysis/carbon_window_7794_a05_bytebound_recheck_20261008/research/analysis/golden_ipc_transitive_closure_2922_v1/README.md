# Golden IPC transitive closure successor (#2922)

This is an additive provenance audit for the retained #2730 route. It does
not modify or rerun #2705, #2730, or #2813 results.

## H/T/D/C/U

- **H:** A complete hash-pinned closure of the retained route will allow the
  task-1 startup gate to reach its ready event without changing route semantics.
- **T:** Enumerate every Python import recursively from the retained
  `golden_desktop_demo.py` and runtime socket entrypoint, recover only files
  whose provenance resolves to the retained #2730 head, and record source and
  destination hashes before any allocation.
- **D:** PASS only after closure, compile/import, private endpoint, and ready
  event all pass. Any missing or ambiguous source is STOP. No task effect is
  part of this gate.
- **C:** Source copies are additive and immutable; Docker uses `--network none`;
  authority remains false; no GUI/input/model task allocation occurs here.
- **U:** Whether the entire historical dependency graph is recoverable from
  the retained commit remains unknown.

## Current stop evidence

The #2813 task-1 attempt passed container-to-host endpoint compatibility and
published a runtime endpoint, then stopped before ready because
`session_v4.py` imported `tile_transport`, which is absent from current
`research/live_control/` and from the existing historical route bundle.

Known historical candidates from retained commit
`01349d7bc76e5635f5568c53ffeec4d9ff49abb1` include:

- `research/observation_tiles/tile_transport.py`
- `research/observation_tiles/image_artifact.py`
- `research/observation_gating/gui_suite.py`
- versioned session/input-owner/pointer-reply modules used by
  `cause_servo_interactive_v4.py`

This list is a lead, not a completed closure. No runtime allocation should
use it until every file is hash-pinned and its imports are audited.
