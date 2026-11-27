# A12 result

`PASS_METHOD_SCOPED`: two simultaneous allowlisted keyboard keys (`a`/38, `d`/40) and Button1 were admitted through the actual process-owner path. An independent X11 observer saw both key presses and ButtonPress plus keymap/pointer-mask down before session-only SIGKILL. Afterward it observed both KeyRelease events and ButtonRelease, with both keymap bits and button mask up. The matched `rpc_eof` receipt is fsynced and recovery-verified with an empty verified close release; the owner thread stopped and service exited 0 without forced termination. Supervisor-requested Xvfb termination exited cleanly 0.

One WSL2/Xvfb run only. Malformed frames, owner-service death, full V15 CLI/outer V39 integration, physical input, game/model feedback and task effect remain untested.
