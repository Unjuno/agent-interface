# Post-R47 integration update — 2026-10-24

The R47 crosswalk identified a missing synthetic composition between the compiled GUI graph and the supervised Win32 standard caller. PR [#9502](https://github.com/Unjuno/agent-interface/pull/9502) is now merged at `7979be472beb3a8bd84c5c83fc98d0a9bc6b9a71` and adds `test_compiled_graph_routes_each_action_through_supervised_dispatch`.

The test composes `compiled_gui.run()` with the real public `interface_dispatch` and `interface_results` routes. It retains the first completed action, changes target generation after the post-effect observation, and verifies that the selected suffix is refused before operation creation or producer start. The graph returns `SAFE_YIELD / execution_refused` with its one-action prefix retained. The focused 122-test set passed in normal and optimized CPython 3.11 on the merged source.

This closes that one construction-check gap only. It is synthetic caller evidence, not a live effect, release/recovery, MAP01, efficiency, or reliability result; the injected verifier does not promote runtime `task_success` from null. The R42–R47 conditions and outcomes are unchanged.
