# A13 owner-service hard-death boundary

A12 established that the owner service can recover two held keys plus Button1 after session-only SIGKILL. A13 changes the death target: after independently verifying the same three holds are down, SIGKILL only the detached owner service while leaving the session child alive. The test asks whether X11 releases input owned by the disconnected XTest client, and requires independent KeyRelease/ ButtonRelease plus keymap/pointer-mask up. It separately records whether a receipt exists; absence of a recovery receipt means this cannot establish verified owner cleanup, even if X11 clears the state.

One candidate invocation; no retries. The scoped result is `PASS_XSERVER_DISCONNECT_RELEASE` only if all input states clear, owner process exits by SIGKILL, session remains alive at observation, and no receipt is falsely claimed. This is a server/client disconnect property, not a process-owner recovery PASS.
