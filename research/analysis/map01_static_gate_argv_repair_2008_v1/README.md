# MAP01 static gate argv repair successor #2008

This source-only successor records the missing-`--out` harness failure from
#1993. It parses the frozen `session_map01_v13.py` option contract and confirms
that a gate must provision a temporary output path before any launcher call.
It does not import the GUI stack, start X11, send input, call a model, or run
MAP01 construction/formal science.

```bash
python research/analysis/map01_static_gate_argv_repair_2008_v1/check_gate.py
```
