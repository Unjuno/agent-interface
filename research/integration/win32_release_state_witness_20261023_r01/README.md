# Win32 release-state query diagnostic R01

This input-free attempt opened a visible, process-owned fixture and recorded an active `Default` input desktop, the exact fixture as foreground, `DESKTOP_HOOKCONTROL` access, `UOI_IO=true`, and `GetAsyncKeyState` returning zero for Ctrl, S and left button. It did not send input. The first packet omitted the fixture thread desktop and token integrity measurements, so it is incomplete for distinguishing all documented zero-return causes. The fresh R02 packet provides those measurements; this raw R01 result remains unchanged.
