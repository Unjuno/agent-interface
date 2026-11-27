# Compiled graph through supervised Win32 caller R01

**Disposition: PASS_SCOPED.** On 2026-10-24, a deterministic local test connected `runtime.core_v1.compiled_gui.run()` to the real `supervised-win32` FastMCP `interface_dispatch` tool. The first graph-selected action completed through standard generation admission and retained custody. After the graph accepted the first effect predicate through the supplied verifier adapter, the target-generation reader changed; the selected suffix was refused by the public dispatch before operation creation and producer start. The graph retained its one-action prefix and returned `SAFE_YIELD / execution_refused`.

The test ran with inert fake process, producer, supervisor and generation-reader components. It establishes public-route composition and stale-generation fail-closed behavior in a deterministic caller test. The test verifier is an injected adapter, not an independent task oracle. The test does not establish real GUI behavior, live release, recovery, MAP01 progress, task success, efficiency or reliability.

The new regression passed with the focused 122-test set in both normal and optimized Python. Exact commands and captured output are in `conditions.json`, `LOCAL_TESTS_NORMAL.txt` and `LOCAL_TESTS_OPTIMIZED.txt`.

Broader runtime and CLI discovery were attempted in the sparse Windows checkout and failed on omitted modules and platform-specific tests; those additional local logs and any generated test residue are preserved separately under `LOCAL_ONLY/` and are not part of this scoped result.

Source change: `runtime/cli_v1/test_mcp_supervised_win32.py`, test `test_compiled_graph_routes_each_action_through_supervised_dispatch`. The production runtime is unchanged.
