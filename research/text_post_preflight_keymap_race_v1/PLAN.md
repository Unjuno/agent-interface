# Post-preflight keymap race v1

Question: can a keymap mutation after the retained executor's final fingerprint check but immediately before first XTest input cross the guard and produce wrong application text?

Fixed formal schedule: three fresh private Xvfb cases, payload `@`: no mutation control, late US→German, late US→French. `deliver()` remains byte-exact retained dependency. A wrapper interposes only its first `xtest.fake_input`; for changed cases a separate X client synchronously installs the target Group1 level0/1 map before forwarding that first event. Receipt must show mutation completion timestamp <= first forwarded input timestamp.

Hard gates: US control exact; German/French `deliver()` remains accepted with emissions >0 yet application text is not `@`; target map hash after mutation equals final map; mutation timing ordering is proven; terminal physical input empty/release verified. This is a deliberately unsafe negative control and does not test a fix.

H: final keymap revalidation is not atomic with first input, so the deterministic post-check mutation crosses the guard. D: negative-result PASS only if both changed cases reproduce wrong effect under the stated timing and all state/release controls pass. C/U: private X11 Group1 level0/1 fault injection only; no natural race frequency, full XKB/Office/Wayland/Windows/macOS/IME/token/product claim.
