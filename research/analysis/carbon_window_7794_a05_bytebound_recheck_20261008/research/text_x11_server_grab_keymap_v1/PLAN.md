# X11 server-grab keymap semantic-serialization v1

Question: does XGrabServer actually close the post-preflight keymap TOCTOU at application-semantic level, not merely delay a competing client's synchronous request completion?

Frozen formal schedule uses 12 fresh private Xvfb/Tk sessions with payload `@`: two US no-mutation controls and five German + five French mutation sessions. Fixed order: US0, DE0, FR0, FR1, DE1, US1, DE2, FR2, FR3, DE3, DE4, FR4. Every changed-session mutator opens its X connection before grab. After grab acquisition and final US-map validation, the mutator request starts; owner sends the already-compiled US XTest plan; while the server remains grabbed the fixture waits 10 ms and reads a Unix-socket shadow that requires no X request; only then owner ungrabs and waits for mutator sync completion.

Per-session hard mechanics gates: final check sees US map; changed mutator request starts before first owner input; all owner input completes before pre-ungrab shadow read; pre-ungrab application shadow/events are empty; ungrab precedes mutator sync completion; final map equals the mutator-observed target map; physical input ends empty. US controls must finish exact `@`.

Decision: `SEMANTIC_SERIALIZATION_PASS` only if every changed session is exact and the application has independently reflected exact `@` before ungrab. `SEMANTIC_SERIALIZATION_FAIL` if mechanics gates pass, pre-ungrab semantic effect is absent, and any changed session finishes with non-`@` text. If no wrong final effect appears but no pre-ungrab semantic acknowledgment exists, return HOLD rather than PASS. This is an engineering discriminator, not a natural race-frequency estimate.

C/U: XGrabServer globally excludes other X clients' request processing while held and may stall the desktop. Private X11 Group1 level0/1 only; no application-model mutation protection, full XKB/IME, Wayland, Windows/macOS, native runtime, token or product-suitability claim.
