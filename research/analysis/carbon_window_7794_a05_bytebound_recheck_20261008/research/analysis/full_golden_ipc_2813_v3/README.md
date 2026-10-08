# Task-1 successor v3

This successor preserves the v1 task wrapper semantics but explicitly imports
the frozen historical route source. It exists because current-main removed the
former root-level `runtime/golden_desktop_demo.py` after v2 was pinned.

The entry gate is source-only. A Docker allocation remains one bounded task-1
attempt and records any infrastructure stop without claiming model or GUI
effects.
