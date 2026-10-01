# Recovery status — 2026-10-01

This directory preserves the exact preformal source capsule from the original
#4319 branch. The source archive and all 39 FREEZE-bound files restored and
verified; the committed restorer reports 16 restored study members. The
14 contract unit tests pass on the available macOS/CPython 3.14.5 host, and
36 restored Python files pass syntax compilation.

**Formal status: STOP before invocation (0/16).** The allocation requires a
Linux private Xvfb/Tk environment with Python-Xlib. Those prerequisites are
absent on the current host; Docker/OrbStack status was unresponsive, so no
container, GUI, public CLI dispatch, or formal batch was started. This source
recovery is not a formal result and makes no claim about the hypothesis.

The original frozen allocation is retained unchanged. Per Issue #4319, do not
rerun or substitute its environment; any future execution needs the stated
allocation and environment without changing its freeze. No result/raw evidence
exists in this recovered branch. The separate historical pilot is not pooled.
