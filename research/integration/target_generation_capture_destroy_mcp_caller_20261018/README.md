# Destroy during capture through the standard MCP caller

Deterministic Fake X caller regression, 2026-10-18. Base `main` source commit: `94d92ec6be8020be71f3d663622d0d651b03df4a`.

## Condition and result

Ubuntu WSL with Python 3.12.3. The test runs the standard MCP server, guarded session and bridge, actual `TargetQueryWorker`, and actual `X11TargetQueries` lifecycle reader. Only the X connection/backend is Fake X.

The fake capture returns an image and then queues `DestroyNotify` before the lifecycle reader's post-capture check. The caller returns `refused` with no source and `input_dispatched=false`; an attempted mint against that sequence is also refused, and the Fake X input emission list remains empty. This closes the missing MCP-composition check for destruction during initial capture; the direct bridge test already covered the lower-level boundary.

The full `runtime.cli_v1.test_mcp_window_lifecycle` module passed **15/15** in normal mode and **15/15** with Python `-O`. Exact process output is retained in `normal.txt` and `optimized.txt`.

## Reproduction

```text
python -m unittest runtime.cli_v1.test_mcp_window_lifecycle
python -O -m unittest runtime.cli_v1.test_mcp_window_lifecycle
```

## Source and output hashes

| File | SHA-256 |
|---|---|
| `runtime/cli_v1/test_mcp_window_lifecycle.py` | `e84ad6fa7c6bd94b84504cf4f8e10d2225e23c2f9f28d45fc4a1ad06c597a6a8` |
| `runtime/guarded_x11_v1/test_window_lifecycle.py` | `b8da342214816f002db0722cd4497097fe28ecda9b91c7e7530f2ccc730177bd` |
| `runtime/cli_v1/mcp_server.py` | `6a4d058fb664088d9970b2a6a462d585105fb2cdaffbd0324d8413388b251805` |
| `runtime/cli_v1/mcp_guarded.py` | `353ee8c77110b4378f58224684172568fbc663b1178e154b22a2960349980e68` |
| `runtime/guarded_x11_v1/bridge.py` | `5f14259a3588e97f23be4b41a364299ecaeadf31cbd493d14ec60a44fae849d9` |
| `runtime/guarded_x11_v1/target_queries.py` | `c7d3667a875383b0f7ad4496a29e86efa547d89979d95324c2528548b6aa33cf` |
| `normal.txt` | `eb452144a137b06a067e529ff118d4e8e51213972d55098c736f5d7cdb90cca5` |
| `optimized.txt` | `2450b14490152ef75d6cfbe24afe8ac3f7485c58eb031b3d0716642ac2fb851e` |

## Scope limits

This is local caller-composition evidence with a synthetic lifecycle event. It does not prove native X event delivery, XID reuse, a physical input/release bound, real application effect, bounded semantic recovery, or efficiency. It used ordinary Ubuntu WSL, not WSLc; no formal allocation, Docker, or live GUI was used. WSLc ownership/allocation status in #7924 remains `UNKNOWN`.
