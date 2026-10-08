# Development calibration

- Remote UNO exposes document RuntimeUID/URL/Text and can activate a document Frame.
- Direct `XSystemDependentWindowPeer.getWindowHandle` is not usable through this separate-process remote UNO path in this environment; empty process-id calls returned void.
- Activating A then B through UNO caused `_NET_ACTIVE_WINDOW` and input focus to converge to distinct Writer XIDs with corroborating titles.
- Positional enumeration is unsafe: repeated fresh sessions with launch order A,B showed UNO component order B,A while X11 client-list order A,B.
- One early order probe failed before observation because its parent process had not propagated the private Xauthority to python-Xlib; authentication propagation was repaired before retained design.
