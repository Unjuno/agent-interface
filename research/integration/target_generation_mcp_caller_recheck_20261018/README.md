# Target-generation evidence through the standard MCP caller

Local current-main recheck, 2026-10-18. Source commit: `8a899106b19b82afa99aa5c1fa0fe8dca18c2d9b`.

## Run

Ubuntu WSL, Python 3.12.3, with the task-local Python environment. The tests use the standard MCP server/session/caller, the actual `TargetQueryWorker` and `X11TargetQueries` lifecycle reader, and a Fake X connection; they do not connect to a real X server or send physical input.

```text
python -m unittest runtime.cli_v1.test_mcp_window_lifecycle
python -O -m unittest runtime.cli_v1.test_mcp_window_lifecycle
```

Both runs exited 0: 14 tests passed in normal mode and 14 in optimized mode. The module includes caller-level checks that retain the observed `window_generation` in `report.json`, then reject an old alias after a `DestroyNotify` for its bound XID without emitting input. This Fake X case does not recreate the XID. The module also covers reparent/remap, blocked lifecycle queries, cancellation/expiry, and isolated observation persistence.

## Retained outputs and source identity

| File | SHA-256 |
|---|---|
| `normal.log` | `b75ea0b652bdd3461b85dec56f7a9529765b052465680f8c664464006d0c0e7f` |
| `optimized.log` | `3e814fc8b3ba992bca20b322e3cdde4324b705be58eab80098b0ff4a94446d59` |
| `runtime/cli_v1/test_mcp_window_lifecycle.py` | `bed094ccb317cf6744cc9dd38e9191e7d48274c93c3b6f234895e4b54cddccd1` |
| `runtime/guarded_x11_v1/test_window_lifecycle.py` | `b8da342214816f002db0722cd4497097fe28ecda9b91c7e7530f2ccc730177bd` |

## Boundary

This is a deterministic caller regression recheck, not a new WSLc allocation or a live GUI experiment. It establishes only that the selected caller preserves the synthetic window-incarnation token and refuses old evidence after the modeled destroy event in these tests. It does not qualify native X server event ordering, real XID reuse, a physical release deadline, real application effects, recovery success, or efficiency. The WSLc allocation/owner status in #7924 remains unknown; no WSLc or Docker action was taken.
