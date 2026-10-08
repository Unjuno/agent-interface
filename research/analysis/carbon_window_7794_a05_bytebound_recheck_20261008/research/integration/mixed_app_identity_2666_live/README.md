# Live mixed-app identity preflight (#2666 successor)

This additive gate reuses the disposable X11 fixture shape from #2499 and
captures typed visible-window records twice. A scoped PASS means the three
disposable clients produced stable records with positive integer
window_id/pid, non-empty title and WM_CLASS, and distinct (window_id, pid)
pairs.

It intentionally does not send input, call a model, infer an application
effect, or satisfy the formal #2499/#2606 acceptance matrix. A failed run is
a preserved discovery blocker, not a reason to replay or silently fall back.
