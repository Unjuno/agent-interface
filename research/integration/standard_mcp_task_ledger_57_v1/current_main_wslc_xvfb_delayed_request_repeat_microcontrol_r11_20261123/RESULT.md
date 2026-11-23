# Current-main WSLc delayed XTEST repeat microcontrol R11

Status: **SCOPED CONTROL PASS; CALLER INTERACTION UNRESOLVED**.

In one fresh private Xvfb, Python Xlib disabled auto-repeat for A while leaving global repeat enabled. A was pressed once; a separate B KeyPress request with a 2,000 ms XTEST delay was queued; A release was queued behind it. An independent event client observed exactly one A KeyPress and one A KeyRelease, plus one B press/release. The blocking sync returned after 2,002.25 ms and an independent keymap read found A/B up. R10/R11 therefore show that simple XTEST holds and delayed requests honor repeat controls in this microcontrol. The R08/R09 standard-caller fixture still produced repeated A effects under matching readback, so the additional caller/harness interaction remains unidentified.

This diagnostic has no MCP runtime, task oracle, production settings or live GUI. It does not pass #57 or justify changing runtime behavior.