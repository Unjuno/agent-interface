# Issue #57 current-main Docker/Linux MCP contract R02

**Status: PASS_CURRENT_MAIN_BOTH_MODES**

Frozen main: `b65b617361efd94494bb472f167f6c966a48464c`
Linux image: `sha256:a3b2b4cd54ca731a86f8d2ba16f1eb833220122c60bfafbdb048e5ad39e50056` (CPython 3.11.2, Docker Server 29.8.1, `--network none`, read-only source mount)

## Result

The public MCP + guarded contract modules each completed all 87 tests normally and under `-O`; both returned exit 0. The independent R08 audit verified raw hashes, source hashes, the complete current-main `runtime/` tree, and the container Python preflight.

| Mode | Tests | Exit | Wall time |
|---|---:|---:|---:|
| normal | 87/87 passed | 0 | 9.008s |
| optimized | 87/87 passed | 0 | 7.197s |

## R01 comparison

R01 used the same image and modules on main `d18eefdb558d8292649f235d61a22bcd5a4e1b53`: normal passed 87/87 in 96.444s, while `-O` passed 86/87 in 13.725s and missed the 2 s dispatch-worker-entry wait. R02 current main passes both modes. Between those main snapshots, the targeted runtime changes were `test_mcp_server.py` (event coordination changed from thread events awaited through `asyncio.to_thread` to `asyncio.Event` set thread-safely), plus unrelated distribution packaging files; `mcp_server.py` and `test_mcp_guarded.py` are unchanged. This makes the test-event boundary a likely explanation for R01's optimized HOLD, but does not prove causality or product-performance change.

R02 suite wall times are much lower than R01. These are test-suite timings for different test-source revisions and are not UI task latency, provider efficiency, or user-visible speedup.

## Scope and remaining gates

This closes the current-main Linux public-MCP contract test HOLD for this cached image. No code changed. No GUI, native input, model/provider, WSLc allocation, task effect, delayed-input recovery, matched cost comparison, runtime distribution, MAP01, or Research Preview acceptance was exercised. Issue #57 remains open for a standard caller task with independently scored effect/release, live provider/token accounting, matched lifecycle efficiency, and transferable recovery evidence.

R01 failure records and R02 preflight/audit setup failures remain preserved; no failed experiment mode was retried. See [`CONDITIONS-r08.json`](CONDITIONS-r08.json), [`AUDIT.json`](AUDIT.json), and raw evidence in `raw-r04/` and `raw-preflight/`.
