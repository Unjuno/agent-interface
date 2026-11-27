# Retained Win32 delayed-input studies

The r01-r10 subdirectories preserve their original sources, conditions, raw
and first results. They are historical evidence, not a generic completion or
quiescence guarantee.

## Additive 2026-11-13 method qualification

The retained r09/r10 reconstruction assigns a Python `MSG.hwnd` attribute,
while the native ctypes field is `MSG.hWnd`. The native destination remains
null in a no-input ABI regression. Their recorded dispatch events therefore
do not prove the intended WndProc consumed the reconstructed message. The
absence of an application effect is not evidence that queued old input is
harmless. No original result or raw file has been changed or replayed.

[R147-R149](../win32_native_queue_effect_boundary_20261113/README.md) preserve
the analogous newly observed fixture crash, its separate bounded orphan
recovery, and a repaired native-queue experiment. R149 retained the original
OS message in the queue and observed one real task effect after the verified
release horizon. It narrows the distinction between input release and later
application effects; it does not establish MAP01 completion or general timing.
