# Docker/Xvfb caller efficiency extension R12

New matched direct-versus-compiled comparison after the R11 harness launch failure. R11 remains a preserved failure and is not pooled as trial data.

Four one-shot arms, no retries: pair 5 direct then compiled (fresh seed 2026102915); pair 6 compiled then direct (fresh seed 2026102916). Conditions inherit R10: pinned image sha256:b473b61c9dda0fab168f4a2118bd1206676dc6913122a3b9193d423426bc0b84; Docker network disabled; read-only rootfs and source; writable evidence; tmpfs /tmp; Xvfb :91; ViZDoom/FreeDoom MAP01; same 600ms W action; same synchronized post-release position oracle; independent keymap down/up; verified empty release receipt; >=0.1 position-change threshold. Only pair identifiers, fresh seeds, config prefix/evidence directory, and the shell interpreter invocation differ from the preserved R10 harness. Python is invoked explicitly as `python3`, verified present with Xlib, ViZDoom 1.3.0 and Xvfb in the pinned image. Timing boundary remains unchanged.

Every arm is attempted once; failures are retained without retry. No model/provider/MCP usage. This is only local descriptive evidence, not broad reliability, product efficiency, MAP01 completion, Windows, or WSLc evidence.
