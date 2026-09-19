# MAP01 import boundary successor #1963

This is the source-only first rung for the runtime/schema failure retained by
#1928 and documented in #1963. It does not modify the parent runtime, start
X11, send input, call a model, or consume a MAP01 allocation.

Run from the repository root:

```bash
python research/analysis/map01_import_boundary_repair_1963_v1/analyze_import_graph.py
python research/analysis/map01_import_boundary_repair_1963_v1/test_repair_candidate.py
```

The result records the flat-name edges `doom.session_v7 -> session_v8` and
`live_control.session_v8 -> session_v7` and preserves the repair constraint:
the successor must introduce an explicit module boundary rather than relying
on `sys.path` order. A later commit may add an import-only candidate repair;
this source-only reproduction is not runtime readiness or MAP01 evidence.

`test_repair_candidate.py` performs only a temporary-copy AST rewrite and
compile check. It is a candidate import-boundary check, not a shared-runtime
repair and not proof that the GUI/session stack is ready.
