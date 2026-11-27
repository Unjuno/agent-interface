# R43 — fresh-generation task effect after R42 release evidence

Status: prepared; no R43 fixture or input has started.

R43 performs one independent standard-MCP task on a fresh native Win32 fixture. It addresses R42's phase-2 harness error by passing the local `user32` handle into the foreground check. A CUA activation receipt and an independently observed foreground HWND are required before any public API observation or dispatch.

R42's 11/11 strict release gate is cited as predecessor evidence from a separate attempt. R43 can establish fresh-generation task-effect and oracle evidence; it cannot establish a paired same-run recovery result, WSLc, MAP01, broad reliability, efficiency, or real-application transfer.
