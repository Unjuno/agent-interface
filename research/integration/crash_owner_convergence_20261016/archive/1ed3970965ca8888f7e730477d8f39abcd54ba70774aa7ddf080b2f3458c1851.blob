# A10 result

`PASS_METHOD_SCOPED`: two simultaneously held allowlisted keys (`a`/38 and `d`/40) were admitted through the actual V15 process backend. An independent X11 observer saw both KeyPress events and both keymap bits down before session-only SIGKILL, then both KeyRelease events and both keymap bits up. The identity-matched fsynced `rpc_eof` receipt verified an empty close release with attempts for both keycodes; the owner thread stopped and service exited 0 without forced termination. Supervisor-requested Xvfb termination exited cleanly with code 0.

This one WSL2/Xvfb result does not test buttons, malformed frames, owner-service death, full V15 CLI, outer V39 cleanup, physical input, game/model feedback, or task completion.
