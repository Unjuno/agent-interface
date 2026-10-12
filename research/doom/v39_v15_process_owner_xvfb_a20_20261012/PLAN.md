# A20 plan

Determine where XTEST ButtonRelease events are delivered on the private Xvfb configuration used by A12/A19. Create a mapped focused client window, move the pointer into it, inject Button1 press and release using a separate connection, independently verify the global pointer mask transitions, and observe events on root, focused client, and the client surface (same XID in this minimal setup). Record the exact recipient(s) and whether root selection is exclusive or additive.

No product recovery candidate is run. One diagnostic invocation, no retry, no physical input, no game/model. This is a construction/diagnostic experiment and does not consume A19.
